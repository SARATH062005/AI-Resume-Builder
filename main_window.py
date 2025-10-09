from PyQt6.QtWidgets import QMainWindow, QTabWidget, QPlainTextEdit
from PyQt6.QtCore import QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Direct imports from sibling files
from ui_layout import UILayout
from event_handlers import EventHandlers

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Resume Builder")
        self.setGeometry(100, 100, 1600, 900)
        self.api_key = None
        
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(1500)
        
        self.right_tabs = QTabWidget()
        self.pdf_viewer = QWebEngineView()
        self.log_viewer_widget = QPlainTextEdit(readOnly=True)
        self.right_tabs.addTab(self.pdf_viewer, "Resume Preview")
        self.right_tabs.addTab(self.log_viewer_widget, "Application Logs")
        
        self.handlers = EventHandlers(self)
        self.ui = UILayout(self, self.handlers)
        
        self.preview_timer.timeout.connect(self.handlers.update_live_preview)
        
        self.ui.add_section("summary")
        self.ui.add_section("experience")
        self.ui.add_section("education")
        self.ui.add_section("skills")
        
        self.handlers.schedule_preview_update()