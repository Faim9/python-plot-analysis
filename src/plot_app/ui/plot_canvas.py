#PySide6 Modules
from PySide6.QtWidgets import QWidget, QVBoxLayout

#pyqtgraph
import pyqtgraph as pg

#Our own modules
from core.parsers import sniff_and_read_dat

#Other imports
from pathlib import Path


class PlotCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plotlayout = QVBoxLayout(self)
        self.plotlayout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(500,500) #Width, Height
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plotlayout.addWidget(self.plot_widget)
        
        self.plot_widget.showGrid(x=True, y=True, alpha=1) 
        self.plot_widget.setLabel('left', 'Y Axis')
        self.plot_widget.setLabel('bottom', 'X Axis')
        
        
        self.current_curve = None

        #Enable antialiasing for smoother lines
        pg.setConfigOptions(antialias=True)

    def plot_file(self, file_path: Path, plot_prefs: dict ={}):
        """Clears the canvas and plots new X/Y arrays using project preferences."""

        self.plot_widget.clear()
        self.plot_widget.setTitle(file_path.name)

        # --- 1. Read Data ---

        data_frame =  sniff_and_read_dat(file_path)

        # --- 2. Apply Theme and preferences ---
        theme = plot_prefs.get("theme", "light")
        
        if theme == "dark":
            self.plot_widget.setBackground('k')  # Black background
            line_color = 'c'                     # Cyan lines for dark theme
        else:
            self.plot_widget.setBackground('w')  # White background
            line_color = 'b'                     # Blue lines for light theme

        lw = plot_prefs.get("line_width", 2.0)
        sz = plot_prefs.get("scatter_size", 5)

        # --- 3. Define plot variables ---

        x_col_idx = plot_prefs.get('column_mapping', {}).get('x_col', 0) #type: ignore
        y_col_idx = plot_prefs.get('column_mapping', {}).get('y_col', 1) #type: ignore

        x_data = data_frame.iloc[:, x_col_idx]
        y_data = data_frame.iloc[:, y_col_idx]
        
        # --- 4. Draw the Plot ---
        pen = pg.mkPen(color=line_color, width=lw)
        
        self.current_curve = self.plot_widget.plot(
            x_data, y_data, 
            pen=pen, 
            symbol='o', 
            symbolSize=sz, 
            symbolBrush=line_color
        )