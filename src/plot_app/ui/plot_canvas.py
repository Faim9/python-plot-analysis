from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Signal
import pyqtgraph as pg
from core.parsers import sniff_and_read_dat
from pathlib import Path

# Color cycle for multi-plot mode
PLOT_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
               '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

class PlotCanvas(QWidget):

    curve_added = Signal(str, str)    # (file_name, color) — tells options widget a curve was added
    curve_removed = Signal(str)       # (file_name)
    canvas_cleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plotlayout = QVBoxLayout(self)
        self.plotlayout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(500, 500)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plotlayout.addWidget(self.plot_widget)
        self.plot_widget.showGrid(x=True, y=True, alpha=1)
        self.plot_widget.setLabel('left', 'Y Axis')
        self.plot_widget.setLabel('bottom', 'X Axis')

        pg.setConfigOptions(antialias=True)

        # Disable scroll zoom, default to rect zoom
        vb = self.plot_widget.getPlotItem().getViewBox()
        vb.setMouseMode(pg.ViewBox.RectMode)
        vb.wheelEvent = lambda ev: None

        # Multi-plot state
        self.multi_mode = False
        self.curves = {}  # {file_name: {'curve': PlotDataItem, 'color': str, 'data': df, 'x_col': int, 'y_col': int}}
        self._color_index = 0

    def _next_color(self):
        color = PLOT_COLORS[self._color_index % len(PLOT_COLORS)]
        self._color_index += 1
        return color

    def set_multi_mode(self, enabled: bool):
        self.multi_mode = enabled
        if not enabled:
            # Switching back to single: clear all but keep nothing
            self.clear_canvas()

    def plot_file(self, file_path: Path, plot_prefs: dict = {}):
        if not self.multi_mode:
            # Single mode: clear everything first
            self.clear_canvas()

        if file_path.name in self.curves:
            return  # Already plotted

        data_frame = sniff_and_read_dat(file_path)

        x_col_idx = plot_prefs.get('column_mapping', {}).get('x_col', 0)
        y_col_idx = plot_prefs.get('column_mapping', {}).get('y_col', 1)
        lw = plot_prefs.get("line_width", 2.0)
        sz = plot_prefs.get("scatter_size", 5)

        color = self._next_color() if self.multi_mode else '#1f77b4'

        x_data = data_frame.iloc[:, x_col_idx]
        y_data = data_frame.iloc[:, y_col_idx]

        pen = pg.mkPen(color=color, width=lw)
        curve = self.plot_widget.plot(
            x_data.values, y_data.values,
            pen=pen,
            symbol='o',
            symbolSize=sz,
            symbolBrush=color,
            name=file_path.name
        )

        self.curves[file_path.name] = {
            'curve': curve,
            'color': color,
            'data': data_frame,
            'x_col': x_col_idx,
            'y_col': y_col_idx,
            'lw': lw,
            'sz': sz
        }

        if not self.multi_mode:
            self.plot_widget.setTitle(file_path.name)

        self.plot_widget.getPlotItem().enableAutoRange()
        self.curve_added.emit(file_path.name, color)

    def remove_curve(self, file_name: str):
        if file_name not in self.curves:
            return
        self.plot_widget.removeItem(self.curves[file_name]['curve'])
        del self.curves[file_name]
        self.curve_removed.emit(file_name)

    def update_curve_columns(self, file_name: str, x_col: int, y_col: int):
        if file_name not in self.curves:
            return
        entry = self.curves[file_name]
        entry['x_col'] = x_col
        entry['y_col'] = y_col
        x_data = entry['data'].iloc[:, x_col]
        y_data = entry['data'].iloc[:, y_col]
        entry['curve'].setData(x_data.values, y_data.values)

    def update_curve_style(self, file_name: str, lw: float = None, sz: int = None, color: str = None):
        if file_name not in self.curves:
            return
        entry = self.curves[file_name]
        lw = lw if lw is not None else entry['lw']
        sz = sz if sz is not None else entry['sz']
        color = color if color is not None else entry['color']
        entry['lw'] = lw
        entry['sz'] = sz
        entry['color'] = color
        entry['curve'].setPen(pg.mkPen(color=color, width=lw))
        entry['curve'].setSymbolSize(sz)
        entry['curve'].setSymbolBrush(color)

    def clear_canvas(self):
        self.plot_widget.clear()
        self.plot_widget.setTitle('')
        self.curves = {}
        self._color_index = 0
        self.canvas_cleared.emit()

    def handle_canvas_buttons_pressed(self, button_pressed):
        match button_pressed:
            case "zoom":
                self.plot_widget.getPlotItem().getViewBox().setMouseMode(pg.ViewBox.RectMode)
            case "pan":
                self.plot_widget.getPlotItem().getViewBox().setMouseMode(pg.ViewBox.PanMode)
            case "reset":
                self.plot_widget.getPlotItem().enableAutoRange()
            case "clear":
                self.clear_canvas()