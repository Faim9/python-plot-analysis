#Importing Pyside6 modules
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeView, QFileSystemModel, QPushButton
from PySide6.QtCore import QDir, Signal

#Other imports
from pathlib import Path


class BaseLeftPanelWidget(QWidget):
    """The parent class for all left-panel tools. Provides a header and a close button."""
    
    def __init__(self, title_text="Panel Title", parent=None):
        super().__init__(parent)
        
        # 1. Master Layout (Vertical - stacks top to bottom)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 2. THE HEADER ROW (Horizontal)
        self.header_layout = QHBoxLayout()
        
        # Create Header Widgets, label, close and refresh button.
        self.title_label = QLabel(f"<b>{title_text}</b>")
        
        self.close_btn = QPushButton("X")
        self.close_btn.setFixedSize(20, 20)  # Keep the button small and square
        self.close_btn.clicked.connect(self.hide)  # Automatically hides the widget when clicked!

        self.refresh_btn = QPushButton('↻')
        self.refresh_btn.setFixedSize(20,20)
        self.refresh_btn.hide() #Start button hidden, and not connected to signals, as it is a placeholder for now.

        # Pack the Header Box
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()  # <--- THE SPRING: Pushes Label Left, Buttons Right
        self.header_layout.addWidget(self.refresh_btn)
        self.header_layout.addWidget(self.close_btn)

        # Add the Header row into the main layout
        self.main_layout.addLayout(self.header_layout)

        
        # 3. The Widget itself
        # Initialize an empty layout here. 
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        # 4. Keep it hidden until the child decides to show
        self.hide()


class DataFolderTreeWidget(BaseLeftPanelWidget):

    file_clicked = Signal(Path, str) #We give the path clicked and which panel was clicked on. In the future to differentiate between DF and AF files

    def __init__(self, parent=None):
        # 1. Call the parent's init, and pass the title!
        super().__init__(title_text="Data Folder:", parent=parent)
        
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
        self.current_data_folder = None #Later give the widget the data folder path to its memory, so refreshing is cleaner

        # 5. Handle file selection and double click
        self.file_tree_view.clicked.connect(self._on_clicked)
        self.file_tree_view.doubleClicked.connect(self._on_double_clicked)

        # 4. Add the tree to the inherited content area
        self.content_layout.addWidget(self.file_tree_view)

    def _on_refresh_clicked(self):
        """Triggered by the refresh button. Uses internal widget saved data folder path"""
        if self.current_data_folder is not None:
            self.refresh(self.current_data_folder)

    def _on_clicked(self, index):

        self.file_clicked.emit(Path(self.model.filePath(index)), 'DF')

        


    def _on_double_clicked(self, index):
        """FileTree focus the double clicked directory, without overwriting self.current_data_folder, so refresh still resets main view."""
        #Useful for navigating more complex data folders without relying on pure FileTree format

        click_path = self.model.filePath(index)

        if not Path(click_path).is_dir():
            return
        
        self.model.setRootPath('') #Clear model's cache

        self.model.setRootPath(click_path)
        self.file_tree_view.setRootIndex(self.model.index(click_path))

        self.show()

        

    def refresh(self, data_folder: str| Path):
        """Clears the list widget and populates it with .dat files from the Data Folder."""
    
        if not Path(data_folder).is_dir:
            return
        self.current_data_folder = data_folder


        data_folder_str = str(data_folder)

        # Set the model's root path to the Data Folder.
        self.model.setRootPath(data_folder_str)
        
        # Lock the TreeView into the Data Folder
        # We tell the UI to set /DF as the absolute ceiling
        self.file_tree_view.setRootIndex(self.model.index(data_folder_str))
        
        # Show Widget
        self.show()




        
        