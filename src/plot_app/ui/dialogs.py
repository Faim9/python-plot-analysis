from PySide6.QtWidgets import QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

class FileConflictDialog(QDialog):
    '''Conflict dialog for import folder function'''

    def __init__(self, conflict_message:str, parent=None, options = None):
        super().__init__(parent)

        if not options:
            options = ['Cancel']

        self.setWindowTitle("File Conflict")
        # Removes the "?" help button on Windows for a cleaner look
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        
        # This will hold the user's final decision
        self.decision = "Cancel" 

        # --- UI Setup ---
        layout = QVBoxLayout(self)
        msg = QLabel(conflict_message)
        layout.addWidget(msg)

        self.btn_layout = QHBoxLayout()

        for button in options:
            str_button = str(button) #Make sure it's a string
            btn = QPushButton(str_button) #Create the button
            btn.clicked.connect(lambda checked=False, decision= str_button: self._close_with(decision)) #Wire it; checked_var absorfs a bool that .clicked sends; decision_var snapshots the str_button var.
            self.btn_layout.addWidget(btn) #Add button to layout

        #Set button layout
        layout.addLayout(self.btn_layout)

    def _close_with(self, decision_string):
        self.decision = decision_string
        self.accept() # Closes the dialog and unpauses the main application