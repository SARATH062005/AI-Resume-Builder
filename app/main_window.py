from PyQt6.QtWidgets import QMainWindow, QTabWidget, QPlainTextEdit, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView

# Updated imports to reflect the new location within the 'app' package
from .ui_layout import UILayout
from .event_handlers import EventHandlers
from logger_setup import setup_logging # Import logger setup

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Resume Builder")
        self.setGeometry(100, 100, 1600, 900)
        self.api_key = None
        
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(1500)
        
        # --- Right Pane Setup ---
        self.right_tabs = QTabWidget()
        
        # Create a container for the PDF viewer and its controls
        pdf_view_container = QWidget()
        pdf_view_layout = QVBoxLayout(pdf_view_container)
        pdf_view_layout.setContentsMargins(0, 5, 0, 0)
        pdf_view_layout.setSpacing(5)

        # Create navigation controls for the WebEngineView
        nav_bar = QHBoxLayout()
        self.back_button = QPushButton("◄ Back")
        self.forward_button = QPushButton("Forward ►")
        self.reload_button = QPushButton("Reload")
        nav_bar.addWidget(self.back_button)
        nav_bar.addWidget(self.forward_button)
        nav_bar.addWidget(self.reload_button)
        nav_bar.addStretch()
        
        # The PDF viewer itself
        self.pdf_viewer = QWebEngineView()
        
        # Add controls and viewer to the container
        pdf_view_layout.addLayout(nav_bar)
        pdf_view_layout.addWidget(self.pdf_viewer)

        # Connect navigation button signals to the viewer's slots
        # --- Connect Navigation Signals ---
        self.back_button.clicked.connect(self.pdf_viewer.back)
        # self.reload_button.clicked.connect(self.handlers.update_live_preview) # Moved below after handlers is initialized
        # Enable/disable back button based on history
        self.pdf_viewer.urlChanged.connect(lambda q: self.back_button.setEnabled(self.pdf_viewer.history().canGoBack()))
        # Enable/disable buttons based on navigation history
        self.pdf_viewer.urlChanged.connect(lambda q: self.forward_button.setEnabled(self.pdf_viewer.history().canGoForward()))
        self.back_button.setEnabled(False) # Initially disabled
        self.forward_button.setEnabled(False) # Initially disabled

        self.log_viewer_widget = QPlainTextEdit() # Will be configured by logger
        setup_logging(self.log_viewer_widget) # Setup logging to use the widget

        # Add the container and the log viewer as tabs
        self.right_tabs.addTab(pdf_view_container, "Resume Preview")
        self.right_tabs.addTab(self.log_viewer_widget, "Application Logs")

        # --- Core UI and Handlers ---
        self.handlers = EventHandlers(self)
        self.ui = UILayout(self, self.handlers)

        self.reload_button.clicked.connect(self.handlers.update_live_preview) # Reload regenerates preview
        self.preview_timer.timeout.connect(self.handlers.update_live_preview)

        self.ui.add_section("summary")
        self.ui.add_section("experience")
        self.ui.add_section("education")
        self.ui.add_section("skills")

        self.handlers.schedule_preview_update()