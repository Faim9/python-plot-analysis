#Importing Pyside6 modules
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeView, QFileSystemModel, QPushButton, QSizeGrip, QCheckBox
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


class PlotOptionsWidget(BaseLeftPanelWidget):

    def __init__(self, plot_canvas,parent=None):
        super().__init__(title_text="" , parent=parent)

        self._canvas = plot_canvas
        self.close_btn.hide() #Dock will handle the button
        self.main_layout.removeWidget(self.header_widget) #Not needed yet

        # Log scale
        self.log_x = QCheckBox("Log X")
        self.log_y = QCheckBox("Log Y")
        self.log_x.toggled.connect(lambda v: plot_canvas.plot_widget.getPlotItem().setLogMode(x=v))
        self.log_y.toggled.connect(lambda v: plot_canvas.plot_widget.getPlotItem().setLogMode(y=v))


        self.content_layout.addWidget(QLabel("Axis"))
        self.content_layout.addWidget(self.log_x)
        self.content_layout.addWidget(self.log_y)
        self.content_layout.addStretch()



        
        