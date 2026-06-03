import sys
from PySide6.QtWidgets import QApplication
from plot_app.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # The MainWindow will handle asking the user for the folder
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()