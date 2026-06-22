#Importing Pyside6 modules
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QFileDialog, QSplitter, QApplication, QDockWidget, QPushButton
from PySide6.QtCore import Qt, QTimer
import PySide6QtAds as ads

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
        self.setGeometry(460, 165, 1000, 750)

    def _setup_menubar(self):
        """Creates the menubar and its actions."""
        menubar = self.menuBar()
        
        # 1. ---Project menu---
        project_menu = menubar.addMenu("Project")
        
        new_project_action = project_menu.addAction("New")
        open_project_action = project_menu.addAction("Open")
        save_project_action = project_menu.addAction("Save")
        close_project_action = project_menu.addAction('Close')

        # 2. --- Import Menu ---
        #Import menu inside Project menu
        import_menu = menubar.addMenu('Import')
        import_folders_action = import_menu.addAction('Folders')
        import_files_action= import_menu.addAction('Files')

        # Connect actions to methods
        new_project_action.triggered.connect(self.new_project)
        open_project_action.triggered.connect(self.open_project)
        save_project_action.triggered.connect(self.save_project)
        close_project_action.triggered.connect(self.close_project)
        import_folders_action.triggered.connect(self._import_folders)
        import_files_action.triggered.connect(self._import_files)

        # 2. ---View menu---
        self.view_menu = menubar.addMenu("View")

        self.view_log_window_action = self.view_menu.addAction('Log window')
        self.view_log_window_action.triggered.connect(self.log_window.show)

        self.view_DF_dock_window_action = self.view_menu.addAction('Data Folder')
        self.view_DF_dock_window_action.triggered.connect(self._view_data_folder_clicked)
        self.view_DF_dock_window_action.setEnabled(False)

    def _setup_toolbar(self):
        """Creates and configures the toolbar."""
        self.toolbar = self.addToolBar("Toolbar")
        self.view_DF_button = QPushButton("DF")
        self.view_DF_button.setFixedSize(20,20)
        self.view_DF_button.setProperty("cssClass", "icon-btn")
        self.view_DF_button.clicked.connect(self._view_data_folder_clicked)

        self.toolbar.addWidget(self.view_DF_button)
    
    def _setup_central_widget(self):
        """Creates and places all visual widgets into layouts using a QSplitter. File tree, options, etc on the left. Plot canvas on the right."""
        self.dock_manager = ads.CDockManager(self)


        # Add the PlotCanvas to the main panel
        self.plot_canvas = PlotCanvas()
        plot_dock = ads.CDockWidget('Plot')
        plot_dock.setWidget(self.plot_canvas)
        self.dock_manager.setCentralWidget(plot_dock)
    
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
    
    def _view_data_folder_clicked(self):
        if not self.project_manager.is_project_loaded:
            return
        
        self.DF_dock.toggleView(True)

    def handle_DF_dock_close(self):
        """Handles the closing of the Data Folder Tree View Dock correctly."""
        
        if self.DF_dock.isFloating():
            self.dock_manager.addDockWidget(
                ads.DockWidgetArea.LeftDockWidgetArea, 
                self.DF_dock
            )

        self.DF_dock.closeDockWidget()
    
    # -------------------------------------------------------------------------
    # UI Logic & Callbacks
    # -------------------------------------------------------------------------

    def new_project(self):
        """Handles the creation of a new project."""
        if self.project_manager.is_project_loaded:
            self.status_bar.showMessage(f'Project already opened. Save and close it before creating a new one.')
            self.app_logger.warning(f'Project already opened. Save and close it before creating a new one.')
            return

        folder = QFileDialog.getExistingDirectory(self, "Select Folder for New Project")

        if not folder:
            return

        success = self.project_manager.create_new_project(folder)

        if success:
            self.open_project(folder)

    def open_project(self,folder):
        """Handles loading an existing project."""
        if self.project_manager.is_project_loaded:
            self.status_bar.showMessage(f'Project already opened. Save and close it before opening a new one.')
            self.app_logger.warning(f'Project already opened. Save and close it before opening a new one.')
            return

        if type(folder) is not str:
            folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")

        success = self.project_manager.load_project(folder)

        if success:
            self.status_bar.showMessage(f"Project loaded from: {folder}")
            self.app_logger.info(f"Project loaded from: {folder}")



            try: # If it's not the first time the user opens a project in current session, the necessary widgets are already loaded.
                self.file_tree.current_data_folder = Path(folder)/'DF' #type:ignore
                self.file_tree.refresh()
                self.DF_dock.show()
                self.view_DF_dock_window_action.setEnabled(True)

                self.app_logger.debug('Successfully opened Data Folder dock.')

            except: # If it's the first time, accessing self.file_tree will send an undefined error. 

                #Initialize the File Tree
                self.file_tree = DataFolderTreeWidget()
                self.file_tree.current_data_folder = Path(folder)/'DF' #type:ignore
                self.file_tree.refresh()
                self.file_tree.file_clicked.connect(self._on_tree_file_clicked)

                #Initialize a Dock container and give it the File Tree Widget showing the data folder
                self.DF_dock = ads.CDockWidget("Data Folder")
                self.DF_dock.setFeature(ads.CDockWidget.DockWidgetFeature.CustomCloseHandling, True)
                self.DF_dock.setWidget(self.file_tree)
                self.dock_manager.addDockWidget(ads.DockWidgetArea.LeftDockWidgetArea, self.DF_dock)

                # Connect the close request signal from File Tree's close button
                self.file_tree.close_requested.connect(self.handle_DF_dock_close)
                self.DF_dock.closeRequested.connect(self.handle_DF_dock_close)

                #Reconnect View Data Folder button
                self.view_DF_dock_window_action.setEnabled(True)

                #Log
                self.app_logger.debug('Successfully opened Data Folder dock.')
        else:
            self.status_bar.showMessage("Failed to load project.")
            self.app_logger.error("Failed to load project.")
            
    def save_project(self) -> bool:
        """Saves the current project settings."""
        return self.project_manager.save_project()

    def close_project(self) -> bool:
        """Saves and closes current project"""
        if self.project_manager.is_project_loaded:
            success = self.project_manager.close_project()
        else:
            self.app_logger.error(f'No project loaded to close.')
            return False

        if success:
            
            #Reset File Tree
            self.file_tree.current_data_folder = None
            self.file_tree.refresh()

            #Close File Tree Dock
            self.handle_DF_dock_close()
            self.view_DF_dock_window_action.setEnabled(False)

            #Reset Plot Canvas
            self.plot_canvas.clear_canvas()

            self.app_logger.info(f'UI reseted.')

            return True
        else:
            return False

    
    