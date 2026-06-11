from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QFileDialog, QListWidget, QSplitter, QLabel
from PySide6.QtCore import Qt
from core.project_manager import ProjectManager
from pathlib import Path
from ui.plot_canvas import PlotCanvas
import numpy as np
from core.parsers import sniff_and_read_dat

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize the project manager
        self.project_manager = ProjectManager()

        # 1. Setup the main window properties
        self._setup_window()
        
        # 2. Create and setup the setup_menubar (file/edit ...), toolbar (icons), central widget and status bar (bottom messages)
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()
        
        # 3. Connect buttons to functions (Signals & Slots)
        self._connect_signals()

    def _setup_window(self):
        """Configures the main window's size, title, and base settings."""
        self.setWindowTitle("Plot App")
        self.setGeometry(100, 100, 1000, 750)

    def _setup_menubar(self):
        """Creates the menubar and its actions."""
        menubar = self.menuBar()
        
        # 1. ---File menu---
        file_menu = menubar.addMenu("File")
        
        new_project_action = file_menu.addAction("New Project")
        open_project_action = file_menu.addAction("Open Project")
        save_project_action = file_menu.addAction("Save Project")

        # Connect actions to methods
        new_project_action.triggered.connect(self.new_project)
        open_project_action.triggered.connect(self.open_project)
        save_project_action.triggered.connect(self.save_project)

        # 2. ---View menu---
        view_menu = menubar.addMenu("View")

        refresh_folder_action = view_menu.addAction("Refresh Folder View")
        refresh_folder_action.triggered.connect(self._refresh_file_list)

    def _setup_toolbar(self):
        """Creates and configures the toolbar."""
        self.toolbar = self.addToolBar("Toolbar")
        
        # Add the refresh button to the toolbar
        refresh_btn = self.toolbar.addAction("↻ Refresh")
        
        # Connect it to the exact same function
        refresh_btn.triggered.connect(self._refresh_file_list)
        
    def _setup_central_widget(self):
        """Creates and places all visual widgets into layouts using a QSplitter."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # The main layout only exists to hold the splitter
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # --- 1. Create the Splitter ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(self.splitter)

        # --- 2. Create the Left Panel (Files) ---
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)

        # Added a label just to make the UI look a bit more polished
        self.file_list_label = QLabel("Data Folder:") 
        self.file_list = QListWidget()

        self.left_layout.addWidget(self.file_list_label)
        self.left_layout.addWidget(self.file_list)

        # --- 3. Create the Right Panel (Plots) ---
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder for our future pyqtgraph canvas
        self.plot_canvas = PlotCanvas()
        self.right_layout.addWidget(self.plot_canvas)

        # --- 4. Add Panels to the Splitter ---
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)

        # --- 5. Set Initial Proportions (25% left, 75% right) ---
        self.splitter.setSizes([250, 750])
    
    def _setup_status_bar(self):
        """Initializes the status bar for displaying messages."""
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready. Create a new project or open an existing one.")

    def _connect_signals(self):
        """Connects UI events (clicks, text changes) to logic functions."""
        self.file_list.itemClicked.connect(self.on_file_selected)

    def _refresh_file_list(self):
        """Clears the list widget and populates it with .dat files from the Data Folder."""
        self.file_list.clear()

        # 1. Safety check: Ensure a project is actually loaded
        if not self.project_manager.is_project_loaded:
            return

        # 2. Get the Data Folder path from the config manager
        data_folder_str = self.project_manager.project_config["data_folder"] #type: ignore
        if not data_folder_str:
            return
            
        data_folder_path = Path(data_folder_str)

        # 3. Read the directory and add files
        if data_folder_path.exists():
            for item in sorted(data_folder_path.iterdir()):
                # Only show actual files (no sub-folders) that end in .dat
                if item.is_file() and item.suffix.lower() == '.dat':
                    self.file_list.addItem(item.name)

    # -------------------------------------------------------------------------
    # UI Logic & Callbacks
    # -------------------------------------------------------------------------

    def new_project(self):
        """Handles the creation of a new project."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder for New Project")

        if not folder:
            return

        success = self.project_manager.create_new_project(folder)

        if success:
            self.status_bar.showMessage(f"Project created at: {folder}")
            self._refresh_file_list()
        else:
            self.status_bar.showMessage("Failed to create project.")

    def open_project(self):
        """Handles loading an existing project."""
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")

        valid_project_folder = self.project_manager._is_folder_valid_project(folder)

        if not valid_project_folder:
            self.status_bar.showMessage("Selected folder is not a valid project folder. Please select a correct project folder or Create a new project.")
            return

        success = self.project_manager.load_project(folder)

        if success:
            self.status_bar.showMessage(f"Project loaded from: {folder}")
            self._refresh_file_list()
        else:
            self.status_bar.showMessage("Failed to load project.")

    def save_project(self):
        """Saves the current project settings."""
        if self.project_manager.project_config:
            self.project_manager.project_config.save()
            self.status_bar.showMessage("Project saved successfully.")
        else:
            self.status_bar.showMessage("No project loaded to save.")

    def save_configs(self):
        """Saves the current project settings."""
        if self.project_manager.project_config:
            self.project_manager.project_config.save()
            self.status_bar.showMessage("Project configs saved successfully.")
        else:
            self.status_bar.showMessage("No project loaded to save configs.")

    def on_file_selected(self, item):
        """Triggered when a file is clicked in the list. Loads the data and updates the plot."""
        filename = item.text()
        data_folder_str = self.project_manager.project_config["data_folder"] #type: ignore

        if not data_folder_str:
            self.status_bar.showMessage("Data folder not set in project config.")
            return
            
        file_path = Path(data_folder_str) / filename

        try:
            df = sniff_and_read_dat(file_path)
            x_col_idx = self.project_manager.project_config["column_mapping"]["x_col"] #type: ignore
            y_col_idx = self.project_manager.project_config["column_mapping"]["y_col"] #type: ignore

            x_data = df.iloc[:, x_col_idx]
            y_data = df.iloc[:, y_col_idx]

            self.plot_canvas.plot_data(x_data, y_data, title=filename)
            self.status_bar.showMessage(f"Plotted: {filename}")
        except Exception as e:
            self.status_bar.showMessage(f"Error loading {filename}: {str(e)}")

    