import logging
import sys
from PyQt6.QtWidgets import QPlainTextEdit

class QPlainTextEditHandler(logging.Handler):
    """A custom logging handler that emits records to a QPlainTextEdit widget."""
    def __init__(self, text_widget: QPlainTextEdit):
        super().__init__()
        self.widget = text_widget
        # Setting properties on a potentially deleted/invalid Qt object
        # can raise a RuntimeError. Guard against that and allow logging
        # to continue to file/console even if the GUI widget is gone.
        try:
            if self.widget is not None:
                self.widget.setReadOnly(True)
        except RuntimeError:
            # Widget was already deleted or is otherwise invalid; detach
            self.widget = None

    def emit(self, record):
        msg = self.format(record)
        # Protect against the widget being deleted between initialization
        # and emit time. Ignore GUI output if the widget is not available.
        if not self.widget:
            return
        try:
            self.widget.appendPlainText(msg)
        except RuntimeError:
            # Widget was deleted; drop GUI logging silently.
            self.widget = None

def setup_logging(gui_log_widget: QPlainTextEdit):
    """Configures logging to file, console, and the GUI."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler
    file_handler = logging.FileHandler('app.log', mode='w')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Console (Stream) Handler
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)

    # GUI Handler
    gui_handler = None
    try:
        if gui_log_widget is not None:
            gui_handler = QPlainTextEditHandler(gui_log_widget)
            gui_handler.setLevel(logging.INFO)
            gui_handler.setFormatter(formatter)
    except Exception:
        # If the GUI handler can't be created (for example the widget
        # was deleted), fall back to file/console logging only.
        gui_handler = None

    # Add all handlers to the root logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    if gui_handler is not None:
        logger.addHandler(gui_handler)