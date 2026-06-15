import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout

class PlotCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plotlayout = QVBoxLayout(self)
        self.plotlayout.setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(500,500) #Width, Height
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plotlayout.addWidget(self.plot_widget)
        
        self.plot_item = self.plot_widget.getPlotItem()
        self.plot_item.showGrid(x=True, y=True, alpha=0.3)
        self.plot_item.setLabel('left', 'Y Axis')
        self.plot_item.setLabel('bottom', 'X Axis')
        
        
        self.current_curve = None

        #Enable antialiasing for smoother lines
        pg.setConfigOptions(antialias=True)

    def plot_data(self, x_data, y_data, title="Data Plot", prefs=None):
        """Clears the canvas and plots new X/Y arrays using project preferences."""

        self.plot_item.clear()
        self.plot_item.setTitle(title)
        
        # --- 1. Fallback Defaults ---
        if prefs is None:
            prefs = {"line_width": 2.0, "scatter_size": 5, "theme": "light"}

        # --- 2. Apply Theme (Background and Text Colors) ---
        if prefs.get("theme") == "dark":
            self.plot_widget.setBackground('k')  # Black background
            line_color = 'c'                     # Cyan lines for dark theme
        else:
            self.plot_widget.setBackground('w')  # White background
            line_color = 'b'                     # Blue lines for light theme

        # --- 3. Extract Line and Scatter Sizes ---
        lw = prefs.get("line_width", 2.0)
        sz = prefs.get("scatter_size", 5)
        
        # --- 4. Draw the Plot ---
        pen = pg.mkPen(color=line_color, width=lw)
        
        self.current_curve = self.plot_item.plot(
            x_data, y_data, 
            pen=pen, 
            symbol='o', 
            symbolSize=sz, 
            symbolBrush=line_color
        )