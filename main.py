import sys

def launch_app():
    """Imports GUI components and launches the main application window."""
    print("Dependencies are satisfied. Launching application...")
    from PyQt6.QtWidgets import QApplication
    # Qt WebEngine components are optional on some systems; import defensively
    try:
        from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings
        webengine_available = True
    except Exception:
        webengine_available = False
    
    # Simple, direct import now
    from app.main_window import MainWindow 
    
    from logger_setup import setup_logging
    import logging

    app = QApplication(sys.argv)
    
    app.setStyleSheet("""
        QGroupBox { font-weight: bold; }
        QFormLayout { padding: 5px; }
        QPushButton { padding: 5px 10px; }
    """)

    if webengine_available:
        try:
            profile = QWebEngineProfile.defaultProfile()
            profile.settings().setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
            # PdfViewerEnabled may not exist in older versions; guard it
            try:
                profile.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)
            except Exception:
                pass
        except Exception:
            # If WebEngine fails to initialize for any reason, continue without it
            webengine_available = False
            print("Warning: Qt WebEngine could not be initialized; preview PDF may not work.")
    
    window = MainWindow()

    setup_logging(window.log_viewer_widget)

    logger = logging.getLogger()
    logger.info("Application starting...")
    window.show()
    logger.info("Application has started successfully.")
    sys.exit(app.exec())

if __name__ == '__main__':
        launch_app()
