import logging
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit

# 1. The Thread-Safe Bridge
class LogSignals(QObject):
    new_log = Signal(str)

# 2. The Custom Handler
class QtLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.signals = LogSignals()
        # We can set the formatter right here to keep things contained!
        formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%H:%M:%S')
        self.setFormatter(formatter)

    def emit(self, record):
        msg = self.format(record)
        self.signals.new_log.emit(msg) # Safely beam it to the Main Thread

# 3. The Window itself
class LoggerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analysis Logs")
        self.resize(600, 400)
        
        # UI Setup
        self.layout = QVBoxLayout(self)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.layout.addWidget(self.text_area)

        # --- THE MAGIC SETUP ---
        # The window sets up its own logger connections!
        self.qt_handler = QtLogHandler()
        self.qt_handler.signals.new_log.connect(self.write_log)

        self.app_logger = logging.getLogger('AppLogger')
        self.app_logger.setLevel(logging.DEBUG)
        self.app_logger.addHandler(self.qt_handler)

    def write_log(self, message: str):
        self.text_area.append(message)
        scrollbar = self.text_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())