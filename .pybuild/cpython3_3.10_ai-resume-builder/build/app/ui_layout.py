from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFormLayout, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QScrollArea, QGroupBox, QLabel, QCheckBox,
    QInputDialog, QToolButton, QStyle, QMainWindow
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QAction
from .ui_components import SectionWidget


# --- Collapsible container widget ---
class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.toggle_button = QToolButton(text=title, checkable=True, checked=False)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle_button.setStyleSheet("""
            QToolButton {
                border: none;
                font-weight: bold;
                padding: 4px;
                color: #222;
            }
        """)

        self.toggle_button.toggled.connect(self.on_toggled)

        self.content_area = QWidget()
        self.content_area.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)

    def on_toggled(self, checked):
        self.content_area.setVisible(checked)
        self.toggle_button.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )


# --- Global style helper ---
def apply_global_styles(app):
    app.setStyle("Fusion")

    app.setStyleSheet("""
        QWidget {
            font-size: 12pt;
            font-family: Segoe UI, Ubuntu, Helvetica, Arial;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 6px;
            margin-top: 10px;
            background-color: #ffffff;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QPushButton {
            border-radius: 6px;
            padding: 6px 10px;
            background-color: #1976d2;
            color: white;
            font-weight: 500;
        }
        QPushButton:hover {
            background-color: #1565c0;
        }
        QLineEdit, QTextEdit, QComboBox {
            border: 1px solid #bbb;
            border-radius: 4px;
            padding: 4px;
            background-color: white;
        }
        QScrollArea {
            border: none;
        }
        QLabel {
            font-weight: normal;
        }
    """)


# --- Main UI Layout ---
class UILayout:
    def __init__(self, main_window: QMainWindow, event_handlers):
        self.win = main_window
        self.eh = event_handlers
        self.setup_ui()

    def setup_ui(self):
        # Toolbar
        toolbar = self.win.addToolBar("Main")
        toolbar.setMovable(False)

        save_action = QAction(QIcon.fromTheme("document-save"), "Save PDF", self.win)
        save_action.triggered.connect(self.eh.save_final_pdf)
        toolbar.addAction(save_action)

        add_section_action = QAction(QIcon.fromTheme("list-add"), "Add Section", self.win)
        add_section_action.triggered.connect(self.add_custom_section_dialog)
        toolbar.addAction(add_section_action)

        ats_action = QAction(QIcon.fromTheme("system-search"), "Check ATS", self.win)
        ats_action.triggered.connect(self.eh.handle_ats_check)
        toolbar.addAction(ats_action)

        # --- Main Layout ---
        central_widget = QWidget()
        self.win.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter()
        main_layout.addWidget(main_splitter)
        
        # --- Left Pane (Forms) ---
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(10)
        
        # --- Collapsible Sections ---
        personal_box = CollapsibleBox("Personal Details")
        personal_box.toggle_button.setChecked(True)
        personal_group = self.create_personal_details_group()
        v = QVBoxLayout(personal_box.content_area)
        v.addWidget(personal_group)
        left_layout.addWidget(personal_box)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        left_layout.addWidget(scroll_area, stretch=1)

        self.win.sections_container = QWidget()
        self.win.sections_layout = QVBoxLayout(self.win.sections_container)
        self.win.sections_layout.setSpacing(15)
        scroll_area.setWidget(self.win.sections_container)
        
        controls_box = CollapsibleBox("Controls & Actions")
        v2 = QVBoxLayout(controls_box.content_area)
        v2.addWidget(self.create_controls_group())
        left_layout.addWidget(controls_box)

        # --- Right Pane (Preview & Logs) ---
        if not getattr(self.win, 'right_tabs', None):
            self.win.right_tabs = QWidget()
        
        main_splitter.addWidget(left_pane)
        main_splitter.addWidget(self.win.right_tabs)

        # DPI-aware scaling
        screen = self.win.screen()
        dpi_scale = screen.logicalDotsPerInch() / 96.0
        main_splitter.setSizes([int(550 * dpi_scale), int(900 * dpi_scale)])

    def create_personal_details_group(self):
        group = QGroupBox()
        layout = QFormLayout(group)
        self.win.name_input = QLineEdit()
        self.win.email_input = QLineEdit()
        self.win.phone_input = QLineEdit()
        self.win.linkedin_input = QLineEdit()
        for widget in [self.win.name_input, self.win.email_input, self.win.phone_input, self.win.linkedin_input]:
            widget.textChanged.connect(self.eh.schedule_preview_update)
        layout.addRow("Name:", self.win.name_input)
        layout.addRow("Email:", self.win.email_input)
        layout.addRow("Phone:", self.win.phone_input)
        layout.addRow("LinkedIn Username:", self.win.linkedin_input)
        return group

    def create_controls_group(self):
        group = QWidget()
        layout = QVBoxLayout(group)

        # --- ATS Checker (Collapsible) ---
        ats_checkbox = QCheckBox("Enable ATS Checker")
        layout.addWidget(ats_checkbox)

        ats_group = QGroupBox("ATS Checker")
        ats_layout = QVBoxLayout(ats_group)
        ats_layout.addWidget(QLabel("Target Job Description:"))

        self.win.job_description_input = QTextEdit(maximumHeight=45)
        ats_layout.addWidget(self.win.job_description_input)

        ats_button = QPushButton("Check ATS Score")
        ats_button.setIcon(self.win.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton))
        ats_button.clicked.connect(self.eh.handle_ats_check)
        ats_layout.addWidget(ats_button)

        ats_group.setVisible(False)
        ats_checkbox.toggled.connect(ats_group.setVisible)
        layout.addWidget(ats_group)

        # --- Other Controls ---
        add_section_button = QPushButton("Add Custom Section")
        add_section_button.setIcon(self.win.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        add_section_button.clicked.connect(self.add_custom_section_dialog)

        api_form = QFormLayout()
        self.win.api_key_button = QPushButton("Set OpenRouter API Key")
        self.win.api_key_button.setIcon(self.win.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        self.win.api_key_button.clicked.connect(self.eh.set_api_key)
        self.win.job_role_input = QLineEdit()
        api_form.addRow(self.win.api_key_button)
        api_form.addRow("Target Job Title:", self.win.job_role_input)

        self.win.template_combo = QComboBox()
        self.win.template_combo.addItems(["moderncv", "classiccv", "moderncv_1"])
        self.win.template_combo.currentTextChanged.connect(self.eh.schedule_preview_update)
        
        save_button = QPushButton("Save Final PDF")
        save_button.setIcon(self.win.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        save_button.clicked.connect(self.eh.save_final_pdf)

        layout.addWidget(add_section_button)
        layout.addLayout(api_form)
        layout.addWidget(self.win.template_combo)
        layout.addWidget(save_button)
        layout.addStretch(1)
        return group

    def add_section(self, section_type, title=None):
        if not title:
            title = section_type.replace('_', ' ').title()
        section = SectionWidget(title, section_type)

        if section_type in ['summary', 'skills', 'custom']:
            content_widget = QTextEdit()
            content_widget.textChanged.connect(self.eh.schedule_preview_update)
            section.content_layout.addWidget(content_widget)
            if section_type == 'summary':
                ai_button = QPushButton("Get AI Suggestion")
                ai_button.setIcon(self.win.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
                ai_button.clicked.connect(lambda: self.eh.handle_targeted_ai_suggestion("summary", content_widget))
                section.content_layout.addWidget(ai_button)
        elif section_type == 'experience':
            section.content = QVBoxLayout()
            add_job_button = QPushButton("Add Job")
            add_job_button.clicked.connect(lambda: self.add_experience_item(section.content))
            section.content_layout.addLayout(section.content)
            section.content_layout.addWidget(add_job_button)
            self.add_experience_item(section.content)
        elif section_type == 'education':
            section.content = QVBoxLayout()
            add_edu_button = QPushButton("Add Degree")
            add_edu_button.clicked.connect(lambda: self.add_education_item(section.content))
            section.content_layout.addLayout(section.content)
            section.content_layout.addWidget(add_edu_button)
            self.add_education_item(section.content)

        section.up_button.clicked.connect(lambda: self.eh.move_section(section, -1))
        section.down_button.clicked.connect(lambda: self.eh.move_section(section, 1))
        section.delete_button.clicked.connect(lambda: self.eh.delete_section(section))
        self.win.sections_layout.addWidget(section)
        return section

    def add_experience_item(self, layout):
        group = QGroupBox("Job")
        form = QFormLayout(group)
        widgets = {
            'title': QLineEdit(),
            'company': QLineEdit(),
            'location': QLineEdit(),
            'years': QLineEdit(),
            'description': QTextEdit()
        }
        for key, widget in widgets.items():
            form.addRow(f"{key.title()}:", widget)
            widget.textChanged.connect(self.eh.schedule_preview_update)
        ai_button = QPushButton("AI Suggestion for this Description")
        ai_button.setIcon(self.win.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        ai_button.clicked.connect(lambda ch, w=widgets, g=group: self.eh.handle_targeted_ai_suggestion("experience_description", w['description'], g))
        form.addRow(ai_button)
        group.setProperty("widgets", widgets)
        layout.addWidget(group)

    def add_education_item(self, layout):
        group = QGroupBox("Degree")
        form = QFormLayout(group)
        widgets = {'degree': QLineEdit(), 'university': QLineEdit(), 'years': QLineEdit()}
        for key, widget in widgets.items():
            form.addRow(f"{key.title()}:", widget)
            widget.textChanged.connect(self.eh.schedule_preview_update)
        group.setProperty("widgets", widgets)
        layout.addWidget(group)
        
    def add_custom_section_dialog(self):
        text, ok = QInputDialog.getText(self.win, "Add Custom Section", "Enter the title for the new section:")
        if ok and text:
            self.add_section("custom", text)
            self.eh.schedule_preview_update()
