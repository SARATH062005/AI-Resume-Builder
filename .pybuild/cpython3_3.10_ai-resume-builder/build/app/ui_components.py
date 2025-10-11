from PyQt6.QtWidgets import (
    QGroupBox, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QTextEdit, QFormLayout, QDialog, QLabel, QScrollArea, QWidget,
    QDialogButtonBox
)
from PyQt6.QtCore import Qt

class SectionWidget(QGroupBox):
    """A self-contained, re-orderable section widget for the UI."""
    def __init__(self, title, section_type, parent=None):
        super().__init__(title, parent)
        self.section_type = section_type
        self.setProperty("section_type", section_type)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 5, 10, 10)
        self.main_layout.setSpacing(10)
        
        control_layout = QHBoxLayout()
        self.up_button = QPushButton("▲ Up")
        self.down_button = QPushButton("▼ Down")
        self.delete_button = QPushButton("✖ Delete")
        self.delete_button.setStyleSheet("background-color: #f44336; color: white;")
        
        control_layout.addStretch()
        control_layout.addWidget(self.up_button)
        control_layout.addWidget(self.down_button)
        control_layout.addWidget(self.delete_button)
        
        self.content_layout = QVBoxLayout()
        
        self.main_layout.addLayout(control_layout)
        self.main_layout.addLayout(self.content_layout)

class AddCustomSectionDialog(QDialog):
    """A dialog to create a custom section with a title and user-defined fields."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Custom Section")
        self.setMinimumWidth(400)
        
        self.main_layout = QVBoxLayout(self)
        
        # Section Title
        self.main_layout.addWidget(QLabel("Section Title:"))
        self.title_input = QLineEdit()
        self.main_layout.addWidget(self.title_input)
        
        # Fields Section
        self.main_layout.addWidget(QLabel("Fields for this section:"))
        self.fields_layout = QVBoxLayout()
        
        add_field_button = QPushButton("＋ Add Field")
        add_field_button.clicked.connect(self.add_field_input)
        self.main_layout.addWidget(add_field_button)
        self.main_layout.addLayout(self.fields_layout)
        
        # Add one field by default
        self.add_field_input()
        
        # OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.main_layout.addWidget(button_box)

    def add_field_input(self):
        field_input = QLineEdit()
        field_input.setPlaceholderText(f"Field Name {self.fields_layout.count() + 1} (e.g., Award Name)")
        self.fields_layout.addWidget(field_input)

    def get_data(self):
        """Returns the dialog data if validation passes."""
        title = self.title_input.text().strip()
        if not title:
            return None # Validation failed

        fields = []
        for i in range(self.fields_layout.count()):
            widget = self.fields_layout.itemAt(i).widget()
            if widget and isinstance(widget, QLineEdit):
                field_text = widget.text().strip()
                if field_text:
                    fields.append(field_text)
        
        if not fields:
            return None # Validation failed

        return {"title": title, "fields": fields}

class ATSResultsDialog(QDialog):
    """A custom dialog to display ATS check results beautifully."""
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ATS Check Results")
        self.setMinimumSize(500, 600)
        layout = QVBoxLayout(self)

        score_label = QLabel(f"<h2>ATS Score: {data.get('score', 'N/A')}/100</h2>")
        score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(score_label)

        summary_label = QLabel(f"<b>Summary:</b> {data.get('match_summary', 'No summary provided.')}")
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)

        def create_feedback_group(title, items, icon):
            group = QGroupBox(title)
            group_layout = QVBoxLayout(group)
            if not items:
                group_layout.addWidget(QLabel("None provided."))
            else:
                for item in items:
                    label = QLabel(f"{icon} {item}")
                    label.setWordWrap(True)
                    group_layout.addWidget(label)
            return group

        layout.addWidget(create_feedback_group("Strengths", data.get('strengths', []), "✅"))
        layout.addWidget(create_feedback_group("Areas for Improvement", data.get('weaknesses', []), "🔧"))
        layout.addWidget(create_feedback_group("Missing Keyword Suggestions", data.get('keyword_suggestions', []), "🔑"))
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button, alignment=Qt.AlignmentFlag.AlignRight)