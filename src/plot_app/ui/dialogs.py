from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

class FileConflictDialog(QDialog):
    '''Conflict dialog for import folder function'''

    def __init__(self, filename, parent=None):
        super().__init__(parent)
        self.setWindowTitle("File Conflict")
        # Removes the "?" help button on Windows for a cleaner look
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        # This will hold the user's final decision
        self.decision = "cancel" 

        # --- UI Setup ---
        layout = QVBoxLayout(self)
        msg = QLabel(f"The file <b>'{filename}'</b> already exists in this folder.<br>What would you like to do?")
        layout.addWidget(msg)

        btn_layout = QHBoxLayout()
        
        # Create buttons
        self.btn_replace = QPushButton("Replace")
        self.btn_replace_all = QPushButton("Replace All")
        self.btn_skip = QPushButton("Skip")
        self.btn_skip_all = QPushButton("Skip All")
        self.btn_cancel = QPushButton("Cancel Import")
        
        # Add buttons to layout
        btn_layout.addWidget(self.btn_replace)
        btn_layout.addWidget(self.btn_replace_all)
        btn_layout.addWidget(self.btn_skip)
        btn_layout.addWidget(self.btn_skip_all)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        # --- Wiring the buttons ---
        # When a button is clicked, lambda sets our decision variable and closes the window
        self.btn_replace.clicked.connect(lambda: self._close_with("replace"))
        self.btn_replace_all.clicked.connect(lambda: self._close_with("replace_all"))
        self.btn_skip.clicked.connect(lambda: self._close_with("skip"))
        self.btn_skip_all.clicked.connect(lambda: self._close_with("skip_all"))
        self.btn_cancel.clicked.connect(lambda: self._close_with("cancel"))

    def _close_with(self, decision_string):
        self.decision = decision_string
        self.accept() # Closes the dialog and unpauses the main application