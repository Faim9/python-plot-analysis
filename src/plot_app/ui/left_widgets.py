#Importing Pyside6 modules
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeView, QFileSystemModel, QPushButton, QSizeGrip, 
                               QCheckBox,QDoubleSpinBox, QSpinBox,QScrollArea, QLineEdit, QFrame,QComboBox, QSizePolicy)
from PySide6.QtCore import QDir, Signal, Qt, QEvent

#Other imports
from pathlib import Path
from utils.file_ops import extract_path


class BaseLeftPanelWidget(QWidget):
    """The parent class for all left-panel tools. Provides a header and a close button."""
    close_requested = Signal() #Emit signal to close instead of .hide() for flexibility. 
    #Example: If the Qwidget is handed to a DockWidget the Dock itself needs to .hide().

    def __init__(self, title_text="Panel Title", parent=None):
        super().__init__(parent)
        
        # 1. Master Layout (Vertical - stacks top to bottom)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 2. THE HEADER ROW (Horizontal)
        # Create Header Widgets, label, close and refresh button.
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(0,0,0,0)
        self.title_label = QLabel(f"<b>{title_text}</b>")
        self.main_layout.addWidget(self.header_widget)
        
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(20, 20)  # Keep the button small and square
        self.close_btn.clicked.connect(self.close_requested.emit)  # Emit close request

        self.refresh_btn = QPushButton('↻')
        self.refresh_btn.setFixedSize(20,20)
        self.refresh_btn.hide() #Start button hidden, and not connected to signals, as it is a placeholder for now.
        
        #Styling buttons
        self.close_btn.setProperty("cssClass", "icon-btn")
        self.refresh_btn.setProperty("cssClass", "icon-btn")

        # Pack the Header Box
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()  # <--- THE SPRING: Pushes Label Left, Buttons Right
        self.header_layout.addWidget(self.refresh_btn)
        self.header_layout.addWidget(self.close_btn)

        
        # 3. The Widget itself
        # Initialize an empty layout here. 
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)
        self.resize_grip = QSizeGrip(self)
        self.main_layout.addWidget(self.resize_grip,0,Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        self.resize_grip.hide()

        # 4. Keep it hidden until the child decides to show
        self.hide()


    
class DataFolderTreeWidget(BaseLeftPanelWidget):

    file_clicked = Signal(Path, str) #We give the path clicked and which panel was clicked on. In the future to differentiate between DF and AF files

    def __init__(self, parent=None):
        # 1. Call the parent's init, and pass the title!
        super().__init__(title_text="DF", parent=parent)
        
        #State variables
        self.current_data_folder = None #Later give the widget the data folder path to its memory, so refreshing is cleaner
        self.current_directory = None

        # 2. Create the FileSystemModel
        self.model = QFileSystemModel()
        self.model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files)

        #Filter to only show .dat files and directories
        self.model.setNameFilters(["*.dat"])
        self.model.setNameFilterDisables(False)  # Hide non-matching files

        # 3. Create the Tree View and set the model
        self.file_tree_view = QTreeView()
        self.file_tree_view.setModel(self.model)
        self.file_tree_view.hideColumn(1)  # Hide Size column
        self.file_tree_view.hideColumn(2)  # Hide Type column
        self.file_tree_view.hideColumn(3)  # Hide Date Modified column

        # 4. Show and connect the refresh button
        self.refresh_btn.show()
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)

        #Create back button
        self.back_btn = QPushButton('↑')
        self.back_btn.setFixedSize(20,20)
        self.back_btn.setProperty("cssClass", "icon-btn")
        self.back_btn.clicked.connect(self._on_back_clicked)
        self.header_layout.insertWidget(2,self.back_btn)
        
        # 5. Handle file selection and double click
        self.file_tree_view.clicked.connect(self._on_file_clicked)
        self.file_tree_view.doubleClicked.connect(self._on_folder_double_clicked)

        # 4. Add the tree to the inherited content area
        self.content_layout.addWidget(self.file_tree_view)

    def _on_refresh_clicked(self):
        """Triggered by the refresh button. Uses internal widget saved data folder path"""
        if self.current_data_folder is not None:
            self.refresh()

    def _on_file_clicked(self, index):

        self.file_clicked.emit(Path(self.model.filePath(index)), 'DF')

        
    def _on_back_clicked(self):

        if self.current_directory == self.current_data_folder:
            return
        
        else:
            index = self.model.index(str(self.current_directory.parent)) #type: ignore
            self._on_folder_double_clicked(index)

    def _on_folder_double_clicked(self, index):
        """FileTree focus the double clicked directory, without overwriting self.current_data_folder, so refresh still resets main view."""
        #Useful for navigating more complex data folders without relying on pure FileTree format

        click_path = self.model.filePath(index)

        path = Path(click_path)

        if not Path(click_path).is_dir():
            return
        
        self.current_directory = path

        self.model.setRootPath('') #Clear model's cache

        self.model.setRootPath(click_path)
        self.file_tree_view.setRootIndex(self.model.index(click_path))
        self.title_label.setText(str(extract_path(path,'DF')))
        self.show()

    def refresh(self):
        """Clears the file tree and populates it with .dat files from the Data Folder. This is called immedietely when the Tree is initialized in main_window."""
        if self.current_data_folder is None:
            #Assume the project got closed. We need to stop showing the files.
            self.current_directory = None
            return
        
        data_folder_str = str(self.current_data_folder)
        self.current_directory = self.current_data_folder
        self.title_label.setText("DF")

        # Set the model's root path to the Data Folder.
        self.model.setRootPath(data_folder_str)
        
        # Lock the TreeView into the Data Folder
        # We tell the UI to set /DF as the absolute ceiling
        self.file_tree_view.setRootIndex(self.model.index(data_folder_str))
        
        # Show Widget
        self.show()

##################################
#Plot Options Class and subclasses
###################################

class CollapsibleSection(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(2)

        self._toggle_btn = QPushButton(f"▾  {title}")
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(True)
        self._toggle_btn.setProperty("cssClass", "section-header")
        self._toggle_btn.clicked.connect(self._on_toggle)
        self._layout.addWidget(self._toggle_btn)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(8, 4, 4, 4)
        self._layout.addWidget(self._content)

    def _on_toggle(self, checked):
        self._content.setVisible(checked)
        label = self._toggle_btn.text()[3:]
        self._toggle_btn.setText(f"{'▾' if checked else '▸'}  {label}")

    def add_widget(self, widget):
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)


class SyncedControl(QWidget):
    """A spinbox (int or float) with an 'All' checkbox beside it.
    When 'All' is checked, the control is enabled and changes apply to all curves.
    When another control owns 'All' and this one doesn't, it becomes greyed out."""

    def __init__(self, label: str, is_float: bool = False, min_val=0, max_val=100,
                 step=1, default=0, parent=None):
        super().__init__(parent)
        self._is_float = is_float
        self._synced = False  # whether this control is in "all" mode

        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)

        self._label = QLabel(label)
        self._label.setFixedWidth(80)
        row.addWidget(self._label)

        if is_float:
            self._spin = QDoubleSpinBox()
            self._spin.setSingleStep(step)
        else:
            self._spin = QSpinBox()

        self._spin.setRange(min_val, max_val)
        self._spin.setValue(default)
        row.addWidget(self._spin)

        self._all_cb = QCheckBox("All")
        self._all_cb.setFixedWidth(40)
        row.addWidget(self._all_cb)

    def value(self):
        return self._spin.value()

    def set_value(self, v, block_signals=True):
        if block_signals:
            self._spin.blockSignals(True)
        self._spin.setValue(v)
        if block_signals:
            self._spin.blockSignals(False)

    def set_locked(self, locked: bool, reason: str = ""):
        """Grey out this control because another 'all' sync is active elsewhere."""
        self._spin.setEnabled(not locked)
        self._all_cb.setEnabled(not locked)
        if locked and reason:
            self._spin.setToolTip(reason)
            self._all_cb.setToolTip(reason)
        else:
            self._spin.setToolTip("")
            self._all_cb.setToolTip("")

    def connect_value(self, slot):
        self._spin.valueChanged.connect(slot)

    def connect_all(self, slot):
        self._all_cb.toggled.connect(slot)

    def is_all(self):
        return self._all_cb.isChecked()

    def set_all_checked(self, checked, block_signals=True):
        if block_signals:
            self._all_cb.blockSignals(True)
        self._all_cb.setChecked(checked)
        if block_signals:
            self._all_cb.blockSignals(False)


class PlotOptionsWidget(BaseLeftPanelWidget):

    def __init__(self, plot_canvas, parent=None):
        super().__init__(title_text="", parent=parent)
        self._canvas = plot_canvas
        self.close_btn.hide()
        self.main_layout.removeWidget(self.header_widget)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        inner = QWidget()
        self._inner_layout = QVBoxLayout(inner)
        self._inner_layout.setContentsMargins(4, 4, 4, 4)
        self._inner_layout.setSpacing(4)
        scroll.setWidget(inner)
        self.content_layout.addWidget(scroll)

        # --- Multi/Single toggle ---
        self._multi_cb = QCheckBox("Multi-plot mode")
        self._multi_cb.toggled.connect(self._on_multi_toggled)
        self._inner_layout.addWidget(self._multi_cb)

        self._add_divider()

        # --- Canvas options ---
        canvas_section = CollapsibleSection("Canvas Options")

        self._log_x = QCheckBox("Log X")
        self._log_y = QCheckBox("Log Y")
        self._log_x.toggled.connect(
            lambda v: plot_canvas.plot_widget.getPlotItem().setLogMode(x=v))
        self._log_y.toggled.connect(
            lambda v: plot_canvas.plot_widget.getPlotItem().setLogMode(y=v))
        canvas_section.add_widget(self._log_x)
        canvas_section.add_widget(self._log_y)

        canvas_section.add_widget(QLabel("X axis title:"))
        self._x_title = QLineEdit("X Axis")
        self._x_title.textChanged.connect(
            lambda t: plot_canvas.plot_widget.setLabel('bottom', t))
        canvas_section.add_widget(self._x_title)

        canvas_section.add_widget(QLabel("Y axis title:"))
        self._y_title = QLineEdit("Y Axis")
        self._y_title.textChanged.connect(
            lambda t: plot_canvas.plot_widget.setLabel('left', t))
        canvas_section.add_widget(self._y_title)

        canvas_section.add_widget(QLabel("X range:"))
        x_range_row = QHBoxLayout()
        self._x_min = QDoubleSpinBox()
        self._x_max = QDoubleSpinBox()
        for sb in (self._x_min, self._x_max):
            sb.setRange(-1e9, 1e9)
            sb.setDecimals(3)
        x_range_row.addWidget(self._x_min)
        x_range_row.addStretch()
        x_range_row.addWidget(QLabel("→"))
        x_range_row.addStretch()
        x_range_row.addWidget(self._x_max)
        canvas_section.add_layout(x_range_row)

        canvas_section.add_widget(QLabel("Y range:"))
        y_range_row = QHBoxLayout()
        self._y_min = QDoubleSpinBox()
        self._y_max = QDoubleSpinBox()
        for sb in (self._y_min, self._y_max):
            sb.setRange(-1e9, 1e9)
            sb.setDecimals(3)
        y_range_row.addWidget(self._y_min)
        y_range_row.addStretch()
        y_range_row.addWidget(QLabel("→"))
        y_range_row.addStretch()
        y_range_row.addWidget(self._y_max)
        canvas_section.add_layout(y_range_row)

        apply_btn = QPushButton("Apply Range")
        apply_btn.clicked.connect(self._apply_range)
        canvas_section.add_widget(apply_btn)

        self._inner_layout.addWidget(canvas_section)
        self._add_divider()

        # --- Curve options ---
        self._curve_section = CollapsibleSection("Curve Options")

        # Combobox to select which curve to edit
        self._curve_combo = QComboBox()
        self._curve_combo.setPlaceholderText("No curves plotted")
        self._curve_combo.currentTextChanged.connect(self._on_curve_selected)
        self._curve_section.add_widget(self._curve_combo)

        # Color indicator
        color_row = QHBoxLayout()
        self._color_dot = QLabel("●")
        self._color_dot.setStyleSheet("font-size: 20px;")
        self._remove_btn = QPushButton("✕ Remove")
        self._remove_btn.setProperty("cssClass", "icon-btn")
        self._remove_btn.clicked.connect(self._on_remove_curve)
        color_row.addWidget(self._color_dot)
        color_row.addStretch()
        color_row.addWidget(self._remove_btn)
        self._curve_section.add_layout(color_row)

        # Synced controls
        self._x_col = SyncedControl("X column:", is_float=False, min_val=0, max_val=99, default=0)
        self._y_col = SyncedControl("Y column:", is_float=False, min_val=0, max_val=99, default=1)
        self._lw    = SyncedControl("Line width:", is_float=True, min_val=0.5, max_val=10.0, step=0.5, default=2.0)
        self._sz    = SyncedControl("Scatter size:", is_float=False, min_val=0, max_val=20, default=5)

        self._synced_controls = {
            'x_col': self._x_col,
            'y_col': self._y_col,
            'lw':    self._lw,
            'sz':    self._sz,
        }

        for key, ctrl in self._synced_controls.items():
            ctrl.connect_value(lambda v, k=key: self._on_value_changed(k, v))
            ctrl.connect_all(lambda checked, k=key: self._on_all_toggled(k, checked))
            self._curve_section.add_widget(ctrl)

        self._inner_layout.addWidget(self._curve_section)
        self._inner_layout.addStretch()

        # Sync state: which controls are in "all" mode
        self._all_synced = {k: False for k in self._synced_controls}

        # Connect canvas signals
        plot_canvas.curve_added.connect(self._on_curve_added)
        plot_canvas.curve_removed.connect(self._on_curve_removed)
        plot_canvas.canvas_cleared.connect(self._on_canvas_cleared)

        self._set_curve_controls_enabled(False)

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _add_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #444;")
        self._inner_layout.addWidget(line)

    def _current_curve_name(self):
        return self._curve_combo.currentText()

    def _set_curve_controls_enabled(self, enabled: bool):
        self._color_dot.setVisible(enabled)
        self._remove_btn.setVisible(enabled)
        for ctrl in self._synced_controls.values():
            ctrl.setVisible(enabled)

    def _load_curve_values(self, file_name: str):
        """Populate controls with the selected curve's stored values."""
        entry = self._canvas.curves.get(file_name)
        if not entry:
            return

        self._color_dot.setStyleSheet(f"color: {entry['color']}; font-size: 20px;")

        n_cols = len(entry['data'].columns)
        self._x_col._spin.setMaximum(n_cols - 1)
        self._y_col._spin.setMaximum(n_cols - 1)

        # Block signals to avoid triggering canvas updates while loading
        self._x_col.set_value(entry['x_col'])
        self._y_col.set_value(entry['y_col'])
        self._lw.set_value(entry['lw'])
        self._sz.set_value(entry['sz'])

        # Restore lock state and tooltips
        for key, ctrl in self._synced_controls.items():
            ctrl.set_all_checked(self._all_synced[key])
            ctrl.set_locked(False)

    def _apply_all_lock_visuals(self):
        """After any 'all' state change, update lock visuals on all controls."""
        for key, ctrl in self._synced_controls.items():
            ctrl.set_locked(False)  # clear first
            ctrl.set_all_checked(self._all_synced[key])

    # -------------------------------------------------------------------------
    # Slots
    # -------------------------------------------------------------------------

    def _on_multi_toggled(self, enabled: bool):
        self._canvas.set_multi_mode(enabled)

    def _apply_range(self):
        vb = self._canvas.plot_widget.getPlotItem().getViewBox()
        vb.setRange(
            xRange=(self._x_min.value(), self._x_max.value()),
            yRange=(self._y_min.value(), self._y_max.value())
        )

    def _on_curve_selected(self, file_name: str):
        if not file_name or file_name not in self._canvas.curves:
            self._set_curve_controls_enabled(False)
            return
        self._set_curve_controls_enabled(True)
        self._load_curve_values(file_name)

    def _on_value_changed(self, key: str, value):
        """Apply value change to current curve, or all curves if synced."""
        if self._all_synced[key]:
            # Apply to all curves
            for name in self._canvas.curves:
                self._apply_to_curve(name, key, value)
        else:
            name = self._current_curve_name()
            if name:
                self._apply_to_curve(name, key, value)

    def _apply_to_curve(self, file_name: str, key: str, value):
        if key in ('x_col', 'y_col'):
            entry = self._canvas.curves.get(file_name, {})
            x = value if key == 'x_col' else entry.get('x_col', 0)
            y = value if key == 'y_col' else entry.get('y_col', 1)
            self._canvas.update_curve_columns(file_name, x, y)
        elif key == 'lw':
            self._canvas.update_curve_style(file_name, lw=value)
        elif key == 'sz':
            self._canvas.update_curve_style(file_name, sz=value)

    def _on_all_toggled(self, key: str, checked: bool):
        self._all_synced[key] = checked
        if checked:
            # Push current value to all curves immediately
            value = self._synced_controls[key].value()
            for name in self._canvas.curves:
                self._apply_to_curve(name, key, value)
        self._apply_all_lock_visuals()

    def _on_remove_curve(self):
        name = self._current_curve_name()
        if name:
            self._canvas.remove_curve(name)

    def _on_curve_added(self, file_name: str, color: str):
        self._curve_combo.addItem(file_name)
        # Auto-select if first curve
        if self._curve_combo.count() == 1:
            self._curve_combo.setCurrentIndex(0)

    def _on_curve_removed(self, file_name: str):
        idx = self._curve_combo.findText(file_name)
        if idx >= 0:
            self._curve_combo.removeItem(idx)
        if self._curve_combo.count() == 0:
            self._set_curve_controls_enabled(False)
            # Lift all sync locks since no curves remain
            for key in self._all_synced:
                self._all_synced[key] = False

    def _on_canvas_cleared(self):
        self._curve_combo.clear()
        self._set_curve_controls_enabled(False)
        for key in self._all_synced:
            self._all_synced[key] = False

        
        