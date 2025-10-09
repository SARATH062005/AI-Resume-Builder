from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFormLayout, QLineEdit,
    QTextEdit, QPushButton, QComboBox, QScrollArea, QGroupBox, QLabel
)
from PyQt6.QtWidgets import QInputDialog
from ui_components import SectionWidget

class UILayout:
    def __init__(self, main_window, event_handlers):
        self.win = main_window
        self.eh = event_handlers
        self.setup_ui()

    def setup_ui(self):
        # --- Main Layout ---
        central_widget = QWidget()
        self.win.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter()
        main_layout.addWidget(main_splitter)
        
        # --- Left Pane (Forms) ---
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- Top Fixed Section (Personal Details) ---
        personal_group = self.create_personal_details_group()
        left_layout.addWidget(personal_group)
        
        # --- Middle Scrollable Section (Dynamic Sections) ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        left_layout.addWidget(scroll_area)
        self.win.sections_container = QWidget()
        self.win.sections_layout = QVBoxLayout(self.win.sections_container)
        self.win.sections_layout.setSpacing(15)
        scroll_area.setWidget(self.win.sections_container)
        
        # --- Bottom Fixed Section (Controls) ---
        controls_group = self.create_controls_group()
        left_layout.addWidget(controls_group)
        
        # --- Right Pane (Preview & Logs) ---
        # The main window may already create the right_tabs (QTabWidget).
        # Only create a placeholder if it doesn't exist to avoid overwriting
        # and deleting widgets created by MainWindow (like the log view).
        if not getattr(self.win, 'right_tabs', None):
            self.win.right_tabs = QWidget()
        # (The rest of this setup is in main_window.py to avoid circular imports)
        
        main_splitter.addWidget(left_pane)
        main_splitter.addWidget(self.win.right_tabs)
        main_splitter.setSizes([600, 1000])

    def create_personal_details_group(self):
        group = QGroupBox("Personal Details")
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
        group = QGroupBox("Controls & Actions")
        layout = QVBoxLayout(group)
        
        # ATS Checker
        ats_group = QGroupBox("ATS Checker")
        ats_layout = QVBoxLayout(ats_group)
        ats_layout.addWidget(QLabel("Target Job Description:"))
        self.win.job_description_input = QTextEdit(minimumHeight=150)
        ats_button = QPushButton("Check ATS Score")
        ats_button.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold;")
        ats_button.clicked.connect(self.eh.handle_ats_check)
        ats_layout.addWidget(self.win.job_description_input)
        ats_layout.addWidget(ats_button)
        layout.addWidget(ats_group)
        
        # Other Controls
        add_section_button = QPushButton("Add Custom Section")
        add_section_button.clicked.connect(self.add_custom_section_dialog)
        
        api_form = QFormLayout()
        self.win.api_key_button = QPushButton("Set OpenRouter API Key")
        self.win.api_key_button.clicked.connect(self.eh.set_api_key)
        self.win.job_role_input = QLineEdit()
        api_form.addRow(self.win.api_key_button)
        api_form.addRow("Target Job Title (for suggestions):", self.win.job_role_input)

        self.win.template_combo = QComboBox()
        self.win.template_combo.addItems(["moderncv", "classiccv", "moderncv_1"])
        self.win.template_combo.currentTextChanged.connect(self.eh.schedule_preview_update)
        
        save_button = QPushButton("Save Final PDF")
        save_button.setStyleSheet("background-color: #008CBA; color: white; font-weight: bold;")
        save_button.clicked.connect(self.eh.save_final_pdf)

        layout.addWidget(add_section_button)
        layout.addLayout(api_form)
        layout.addWidget(self.win.template_combo)
        layout.addWidget(save_button)
        return group

    def add_section(self, section_type, title=None):
        if not title: title = section_type.replace('_', ' ').title()
        section = SectionWidget(title, section_type)

        if section_type in ['summary', 'skills', 'custom']:
            content_widget = QTextEdit()
            content_widget.textChanged.connect(self.eh.schedule_preview_update)
            section.content_layout.addWidget(content_widget)
            if section_type == 'summary':
                ai_button = QPushButton("Get AI Suggestion")
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
        widgets = {'title': QLineEdit(), 'company': QLineEdit(), 'location': QLineEdit(), 'years': QLineEdit(), 'description': QTextEdit()}
        for key, widget in widgets.items():
            form.addRow(f"{key.title()}:", widget)
            widget.textChanged.connect(self.eh.schedule_preview_update)
        ai_button = QPushButton("AI Suggestion for this Description")
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