import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from ui.logger_window import LoggerWindow

def main():
    app = QApplication(sys.argv)

    log_window = LoggerWindow()
    
    window = MainWindow(log_window)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()