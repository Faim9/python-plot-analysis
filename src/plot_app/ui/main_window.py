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

    # -------------------------------------------------------------------------
    # Connecting signals and logic
    # -------------------------------------------------------------------------

    def _import_folders(self):
        '''Import entire folder structures to the Data Folder, /DF'''

        if not self.project_manager.is_project_loaded:
            self.status_bar.showMessage(f"Error. Project not loaded yet. Open or create a new one to import data.")
            return
        
        imported_directory = QFileDialog.getExistingDirectory(self, "Select folder or file to import")
        if not imported_directory: return

        source_folder = Path(imported_directory)
        aimed_directory = self.project_manager.active_project_path / 'DF' / source_folder.name

        self.status_bar.showMessage(f'Importing {imported_directory} whole structure and files to {aimed_directory}')

        # State variables for the import
        skip_all = False
        replace_all = False
        import_cancelled = False

        # --- THE INTERCEPTOR ---
        def smart_copy(src, dst):
            nonlocal skip_all,replace_all,import_cancelled

            # If the user previously clicked cancel, immediately abort further copies
            if import_cancelled:
                return 

            # Check if there is a collision
            if Path(dst).exists():
                if skip_all:
                    return  # Do nothing, just return
                
                if not replace_all:
                    # Pop the dialog! (This pauses the script until they click)
                    dialog = FileConflictDialog(Path(src).name, self)
                    dialog.exec()
                    
                    # Process their decision
                    if dialog.decision == "cancel":
                        import_cancelled = True
                        return
                    elif dialog.decision == "skip_all":
                        skip_all = True
                        return
                    elif dialog.decision == "skip":
                        return
                    elif dialog.decision == "replace_all":
                        replace_all = True
                    # If it's "replace", we just let it fall through to the copy function below
            
            # If we reach here, it's safe to overwrite or the file is new
            copy2(src, dst)


        try:
            copytree(imported_directory,aimed_directory, dirs_exist_ok=True,copy_function=smart_copy)
            if import_cancelled:
                self.status_bar.showMessage(f'Import canceled.')
            else: self.status_bar.showMessage(f'Import sucess.')
        except Exception as e:
            self.status_bar.showMessage(f'Error during folder import: {e}.')

    def _import_files(self):
        '''Import files .dat to the Data Folder, /DF'''
        
        if not self.project_manager.is_project_loaded:
            self.status_bar.showMessage(f"Error. Project not loaded yet. Open or create a new one to import data.")
            return
        
        imported_files, _ = QFileDialog.getOpenFileNames(self, 'Import Files', filter= 'Data Files (*.dat);;All Files (*.*)')

        if not imported_files:
            self.status_bar.showMessage(f'No files selected to import.')
            return

        aimed_directory = self.project_manager.active_project_path / 'DF'

        self.status_bar.showMessage(f'Importing {len(imported_files)} to {aimed_directory}')

        #2. Safely copy each file
        for file_path_str in imported_files:
            source_file = Path(file_path_str)
            intended_destination_file = aimed_directory / source_file.name
            destination_file = get_safe_path_destination(intended_destination_file)
            
            try:
                # Copy the file and preserve its metadata
                copy2(source_file, destination_file)
            except Exception as e:
                self.status_bar.showMessage(f"Error copying {source_file.name}: {e}")

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
                self.plot_canvas.plot_file(file_path, self.project_manager.project_config['plot_prefs']) 
                self.status_bar.showMessage(f"Plotted: {file_path.name}")
            except Exception as e:
                self.status_bar.showMessage(f"Error loading {file_path.name}: {str(e)}")

    def _handle_theme_change(self, theme_name:str):

        theme_file_path = Path(__file__).parent.parent / 'assets' / 'app_themes' / theme_name
        print(theme_file_path)

        if theme_file_path.exists():

            try:
                with open(theme_file_path,'r') as theme:
                    qss_string = theme.read()
                
                app = QApplication.instance()
                app.setStyleSheet(qss_string)

            except Exception as e:
                self.status_bar.showMessage(f'Failed to set theme: {e}.')
                return
            
        else: 
            self.status_bar.showMessage(f'The theme {theme_name} is not recognised.') 
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
            self.file_tree.refresh(Path(folder)/'DF')
            self.file_tree.file_clicked.connect(self._on_tree_file_clicked)
        else:
            self.status_bar.showMessage("Failed to create project.")

    def open_project(self):
        """Handles loading an existing project."""
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")

        success = self.project_manager.load_project(folder)

        if success:
            self.status_bar.showMessage(f"Project loaded from: {folder}")
            self.file_tree = DataFolderTreeWidget()
            self.left_layout.addWidget(self.file_tree)
            self.file_tree.refresh(Path(folder)/'DF')
            self.file_tree.file_clicked.connect(self._on_tree_file_clicked)
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

    
    