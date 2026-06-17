#Importing Pyside6 modules
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QFileDialog, QSplitter, QApplication
from PySide6.QtCore import Qt

#Importing our own modules
from core.project_manager import ProjectManager
from ui.plot_canvas import PlotCanvas
from ui.left_widgets import DataFolderTreeWidget
from ui.dialogs import FileConflictDialog
from utils.file_ops import get_safe_path_destination

#Other imports
from pathlib import Path
from shutil import copy2, copytree
import logging

class MainWindow(QMainWindow):
    def __init__(self,log_window):
        super().__init__()

        #Save log window so we can show on demand
        self.log_window = log_window

        self.app_logger = logging.getLogger('AppLogger')
        
        # Initialize the project manager
        self.project_manager = ProjectManager()

        # 1. Setup the main window properties
        self._setup_window()
        
        # 2. Create and setup the setup_menubar (file/edit ...), toolbar (icons), central widget and status bar (bottom messages)
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_central_widget()
        self._setup_status_bar()

        #Set theme
        self._handle_theme_change('dark.qss')

    def _setup_window(self):
        """Configures the main window's size, title, and base settings."""
        self.setWindowTitle("Plot App")
        self.setGeometry(0, 0, 1000, 750)

    def _setup_menubar(self):
        """Creates the menubar and its actions."""
        menubar = self.menuBar()
        
        # 1. ---File menu---
        file_menu = menubar.addMenu("File")
        
        new_project_action = file_menu.addAction("New Project")
        open_project_action = file_menu.addAction("Open Project")
        save_project_action = file_menu.addAction("Save Project")

        #Import menu inside File menu
        import_menu = file_menu.addMenu('Import')
        import_folders_action = import_menu.addAction('Folders')
        import_files_action= import_menu.addAction('Files')

        # Connect actions to methods
        new_project_action.triggered.connect(self.new_project)
        open_project_action.triggered.connect(self.open_project)
        save_project_action.triggered.connect(self.save_project)
        import_folders_action.triggered.connect(self._import_folders)
        import_files_action.triggered.connect(self._import_files)

        # 2. ---View menu---
        view_menu = menubar.addMenu("View")

        view_log_window_action = view_menu.addAction('Log window')
        view_log_window_action.triggered.connect(self.log_window.show)

    def _setup_toolbar(self):
        """Creates and configures the toolbar."""
        #self.toolbar = self.addToolBar("Toolbar")

        pass
        
    def _setup_central_widget(self):
        """Creates and places all visual widgets into layouts using a QSplitter. File tree, options, etc on the left. Plot canvas on the right."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # The main layout only exists to hold the splitter
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(5, 5, 5, 5)

        # --- 1. Create the Splitter ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False) #Collapsing either side is now impossible
        self.main_layout.addWidget(self.splitter)

        # --- 2. Create the Left Panel---
        self.left_panel = QWidget()
        self.left_panel.setMinimumSize(50,100) #Width, Height
        self.left_layout = QVBoxLayout(self.left_panel)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        
        
        # --- 3. Create the Right Panel (Plots) ---
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the PlotCanvas to the right panel
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
        self.app_logger.info("Application initiated. Ready to open or create a project.")
        

    # -------------------------------------------------------------------------
    # Connecting signals and logic
    # -------------------------------------------------------------------------

    def _import_folders(self):
        '''Import entire folder structures to the Data Folder, /DF'''

        if not self.project_manager.is_project_loaded:
            self.status_bar.showMessage(f"Error. Project not loaded yet. Open or create a new one to import data.")
            self.app_logger.warning(f'Project not loaded yet. Open or create a new one to import data.')
            return
        
        imported_directory = QFileDialog.getExistingDirectory(self, "Select folder or file to import")
        if not imported_directory: 
            self.app_logger.debug(f'No directory.')
            return

        source_folder = Path(imported_directory)

        self.status_bar.showMessage(f'Importing {imported_directory} whole structure and files to /DF.')
        self.app_logger.info(f'Importing {imported_directory} whole structure and files to /DF.')

        self.project_manager.import_folder(source_folder)

        

    def _import_files(self):
        '''Import files .dat to the Data Folder, /DF'''
        
        #Check project loaded
        if not self.project_manager.is_project_loaded:
            self.status_bar.showMessage(f"Error. Project not loaded yet. Open or create a new one to import data.")
            self.app_logger.error(f'Project not loaded yet. Open or create a new one to import data.')
            return
        
        #Select files
        imported_files, _ = QFileDialog.getOpenFileNames(self, 'Import Files', filter= 'Data Files (*.dat);;All Files (*.*)')

        #Check files
        if not imported_files:
            self.status_bar.showMessage(f'No files selected to import.')
            self.app_logger.info(f'No files selected to import. Aborting.')
            return


        #Import files
        self.project_manager.import_files(imported_files)


    def _on_tree_file_clicked(self, file_path: Path, file_tree_object: str):
        """Triggered when a file is clicked in a File Tree View. It hands the file path to the appropriate object (ex: data folder files are handed to plot_canvas)"""
        #Some checks first
        if not self.project_manager.is_project_loaded:
            return

        #If it's a directory, ignore the click (we are only concerned with files for the moment)
        if file_path.is_dir():
            return
        
        if file_path.suffix == '.dat' and file_tree_object == 'DF': #Hand to Plot_canvas
            try:
                self.plot_canvas.plot_file(file_path, self.project_manager.project_config['plot_prefs'])  #type:ignore
                self.status_bar.showMessage(f"Plotted: {file_path.name}")
            except Exception as e:
                self.status_bar.showMessage(f"Error loading {file_path.name}: {str(e)}")

    def _handle_theme_change(self, theme_name:str):

        theme_file_path = Path(__file__).parent.parent / 'assets' / 'app_themes' / theme_name
        self.app_logger.debug(f'Setting {theme_name} theme.')

        if theme_file_path.exists():

            try:
                with open(theme_file_path,'r') as theme:
                    qss_string = theme.read()
                
                app = QApplication.instance()
                app.setStyleSheet(qss_string) #type: ignore

            except Exception as e:
                self.status_bar.showMessage(f'Failed to set theme: {e}.')
                self.app_logger.exception(f'Failed to set the theme: {str(e)}')
                return
            
        else: 
            self.status_bar.showMessage(f'The theme {theme_name} is not recognised.') 
            self.app_logger.error(f'The theme {theme_name} is not recognised.')
            return
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
            self.file_tree = DataFolderTreeWidget()
            self.left_layout.addWidget(self.file_tree)
            self.file_tree.current_data_folder = Path(folder)/'DF' #type:ignore
            self.file_tree.refresh()
            self.file_tree.file_clicked.connect(self._on_tree_file_clicked)
        else:
            self.status_bar.showMessage("Failed to create project.")

    def open_project(self):
        """Handles loading an existing project."""
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")

        success = self.project_manager.load_project(folder)

        if success:
            self.status_bar.showMessage(f"Project loaded from: {folder}")
            self.app_logger.info(f"Project loaded from: {folder}")
            self.file_tree = DataFolderTreeWidget()
            self.left_layout.addWidget(self.file_tree)
            self.file_tree.current_data_folder = Path(folder)/'DF' #type:ignore
            self.file_tree.refresh()
            self.file_tree.file_clicked.connect(self._on_tree_file_clicked)
        else:
            self.status_bar.showMessage("Failed to load project.")
            self.app_logger.error("Failed to load project.")
            
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

    
    