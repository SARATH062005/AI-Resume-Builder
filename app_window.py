import sys
import os
import json
import logging
import time
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QFormLayout, QLineEdit, QTextEdit, QPushButton, QComboBox, QScrollArea,
    QGroupBox, QMessageBox, QInputDialog, QPlainTextEdit, QTabWidget,
    QSizePolicy, QDialog, QLabel
)
from PyQt6.QtCore import QUrl, Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWebEngineWidgets import QWebEngineView

from openrouter_service import get_targeted_ai_suggestion, get_ats_score_and_feedback
from latex_service import generate_latex_resume

logger = logging.getLogger()

# (SectionWidget class remains the same)
class SectionWidget(QGroupBox):
    def __init__(self, title, section_type, parent=None):
        super().__init__(title, parent)
        self.section_type = section_type
        # ... (rest of the class is unchanged)
        self.setProperty("section_type", section_type)
        self.main_layout = QVBoxLayout(self)
        self.control_layout = QHBoxLayout()
        self.content_layout = QVBoxLayout()
        self.up_button = QPushButton("Up")
        self.down_button = QPushButton("Down")
        self.delete_button = QPushButton("Delete")
        self.delete_button.setStyleSheet("background-color: #f44336; color: white;")
        self.control_layout.addStretch()
        self.control_layout.addWidget(self.up_button)
        self.control_layout.addWidget(self.down_button)
        self.control_layout.addWidget(self.delete_button)
        self.main_layout.addLayout(self.control_layout)
        self.main_layout.addLayout(self.content_layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... (initial setup is the same)
        self.setWindowTitle("AI Resume Builder")
        self.setGeometry(100, 100, 1600, 900)
        self.api_key = None
        
        self.preview_timer = QTimer(self)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.setInterval(1500)
        self.preview_timer.timeout.connect(self.update_live_preview)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_splitter = QSplitter()
        main_layout.addWidget(main_splitter)
        
        left_pane = QWidget()
        left_layout = QVBoxLayout(left_pane)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        left_layout.addWidget(scroll_area)
        self.sections_container = QWidget()
        self.sections_layout = QVBoxLayout(self.sections_container)
        scroll_area.setWidget(self.sections_container)
        
        personal_group = QGroupBox("Personal Details")
        personal_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.linkedin_input = QLineEdit()
        for widget in [self.name_input, self.email_input, self.phone_input, self.linkedin_input]:
            widget.textChanged.connect(self.schedule_preview_update)
        personal_layout.addRow("Name:", self.name_input)
        personal_layout.addRow("Email:", self.email_input)
        personal_layout.addRow("Phone:", self.phone_input)
        personal_layout.addRow("LinkedIn Username:", self.linkedin_input)
        personal_group.setLayout(personal_layout)
        left_layout.insertWidget(0, personal_group)

        self.add_section("summary")
        self.add_section("experience")
        self.add_section("education")
        self.add_section("skills")
        
        controls_group = QGroupBox("Controls & Actions")
        controls_layout = QVBoxLayout(controls_group)

        # --- NEW ATS CHECKER WIDGETS ---
        ats_group = QGroupBox("ATS Checker")
        ats_layout = QVBoxLayout(ats_group)
        self.job_description_input = QTextEdit()
        self.job_description_input.setPlaceholderText("Paste the full target job description here for an ATS score...")
        self.job_description_input.setFixedHeight(150) # Give it a decent size
        ats_button = QPushButton("Check ATS Score")
        ats_button.setStyleSheet("background-color: #ff9800; color: white; font-weight: bold; padding: 5px;")
        ats_button.clicked.connect(self.handle_ats_check)
        ats_layout.addWidget(QLabel("Target Job Description:"))
        ats_layout.addWidget(self.job_description_input)
        ats_layout.addWidget(ats_button)
        controls_layout.addWidget(ats_group)
        # -------------------------------

        add_section_button = QPushButton("Add Custom Section")
        add_section_button.clicked.connect(self.add_custom_section_dialog)
        controls_layout.addWidget(add_section_button)

        api_form = QFormLayout()
        self.api_key_button = QPushButton("Set OpenRouter API Key")
        self.api_key_button.clicked.connect(self.set_api_key)
        self.job_role_input = QLineEdit() # This is still useful for targeted suggestions
        api_form.addRow(self.api_key_button)
        api_form.addRow("Target Job Title (for suggestions):", self.job_role_input)
        controls_layout.addLayout(api_form)

        self.template_combo = QComboBox()
        self.template_combo.addItems(["moderncv", "classiccv", "moderncv_1"])
        self.template_combo.currentTextChanged.connect(self.schedule_preview_update)
        controls_layout.addWidget(self.template_combo)
        
        save_button = QPushButton("Save Final PDF")
        save_button.setStyleSheet("background-color: #008CBA; color: white; font-weight: bold; padding: 5px;")
        save_button.clicked.connect(self.save_final_pdf)
        controls_layout.addWidget(save_button)
        left_layout.addWidget(controls_group)

        self.right_tabs = QTabWidget()
        self.pdf_viewer = QWebEngineView()
        self.right_tabs.addTab(self.pdf_viewer, "Resume Preview")
        self.log_viewer_widget = QPlainTextEdit(readOnly=True)
        self.right_tabs.addTab(self.log_viewer_widget, "Application Logs")
        main_splitter.addWidget(left_pane)
        main_splitter.addWidget(self.right_tabs)
        main_splitter.setSizes([600, 1000])
        
        self.schedule_preview_update()

    def handle_ats_check(self):
        logger.info("'Check ATS Score' button clicked.")
        if not self.api_key:
            QMessageBox.warning(self, "API Key Missing", "Please set your OpenRouter API key first.")
            return
        job_description = self.job_description_input.toPlainText()
        if not job_description:
            QMessageBox.warning(self, "Input Missing", "Please paste the target job description into the ATS Checker box.")
            return
            
        resume_data = self.gather_data()
        QMessageBox.information(self, "AI Request", "Analyzing your resume against the job description... This may take a moment.")
        
        response_raw = get_ats_score_and_feedback(self.api_key, job_description, resume_data)
        
        try:
            # Clean the response in case the AI wraps it in markdown
            if "```json" in response_raw:
                response_raw = response_raw.split("```json\n")[1].rsplit("```", 1)
            
            # Find the JSON object within the text
            match = re.search(r'\{.*\}', response_raw, re.DOTALL)
            if not match:
                raise json.JSONDecodeError("No JSON object found in the response.", response_raw, 0)
            
            data = json.loads(match.group(0))
            if "error" in data:
                raise Exception(data["error"])

            self.show_ats_results_dialog(data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse ATS JSON response: {e}\nRaw response:\n{response_raw}")
            QMessageBox.critical(self, "AI Error", "Could not parse the AI's response. Check logs for details.")
            self.right_tabs.setCurrentIndex(1)
        except Exception as e:
            logger.error(f"An error occurred during ATS check: {e}")
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def show_ats_results_dialog(self, data):
        dialog = QDialog(self)
        dialog.setWindowTitle("ATS Check Results")
        dialog.setMinimumSize(500, 600)
        layout = QVBoxLayout(dialog)

        # Score
        score_label = QLabel(f"<h2>ATS Score: {data.get('score', 'N/A')}/100</h2>")
        score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(score_label)

        # Summary
        summary_label = QLabel(f"<b>Summary:</b> {data.get('match_summary', 'No summary provided.')}")
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)

        # Strengths
        strengths_group = QGroupBox("Strengths")
        strengths_layout = QVBoxLayout(strengths_group)
        for item in data.get('strengths', []):
            strengths_layout.addWidget(QLabel(f"✅ {item}"))
        layout.addWidget(strengths_group)

        # Weaknesses
        weaknesses_group = QGroupBox("Areas for Improvement")
        weaknesses_layout = QVBoxLayout(weaknesses_group)
        for item in data.get('weaknesses', []):
            weaknesses_layout.addWidget(QLabel(f"🔧 {item}"))
        layout.addWidget(weaknesses_group)

        # Keywords
        keywords_group = QGroupBox("Missing Keyword Suggestions")
        keywords_layout = QVBoxLayout(keywords_group)
        for item in data.get('keyword_suggestions', []):
            keywords_layout.addWidget(QLabel(f"🔑 {item}"))
        layout.addWidget(keywords_group)
        
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)
        
        dialog.exec()

    # (All other methods like schedule_preview_update, save_final_pdf, add_section, gather_data, etc., remain the same as the previous step)
    # ... PASTE ALL OTHER METHODS FROM THE PREVIOUS RESPONSE HERE ...
    def schedule_preview_update(self):
        self.preview_timer.start()

    def update_live_preview(self):
        logger.info("User paused typing. Updating live preview...")
        resume_data = self.gather_data()
        template_name = self.template_combo.currentText()
        pdf_path = generate_latex_resume(resume_data, template_name, is_preview=True)
        if pdf_path:
            qurl = QUrl.fromLocalFile(os.path.abspath(pdf_path))
            qurl.setQuery(f"cache_buster={int(time.time())}")
            self.pdf_viewer.setUrl(qurl)
            self.right_tabs.setCurrentIndex(0)
        else:
            logger.error("Live preview update failed.")
    
    def save_final_pdf(self):
        logger.info("'Save Final PDF' button clicked.")
        resume_data = self.gather_data()
        template_name = self.template_combo.currentText()
        pdf_path = generate_latex_resume(resume_data, template_name, is_preview=False)
        if pdf_path:
            full_path = os.path.abspath(pdf_path)
            QMessageBox.information(self, "PDF Saved", f"Successfully saved the final resume to:\n{full_path}")
        else:
            QMessageBox.critical(self, "PDF Generation Failed", "Could not save the final PDF. Check the 'Application Logs' tab for details.")
            self.right_tabs.setCurrentIndex(1)

    def add_section(self, section_type, title=None):
        if not title: title = section_type.replace('_', ' ').title()
        section = SectionWidget(title, section_type)
        if section_type in ['summary', 'skills', 'custom']:
            content_widget = QTextEdit()
            content_widget.textChanged.connect(self.schedule_preview_update)
            section.content_layout.addWidget(content_widget)
            if section_type == 'summary':
                ai_button = QPushButton("Get AI Suggestion")
                ai_button.clicked.connect(lambda: self.handle_targeted_ai_suggestion("summary", content_widget))
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
        section.up_button.clicked.connect(lambda: self.move_section(section, -1))
        section.down_button.clicked.connect(lambda: self.move_section(section, 1))
        section.delete_button.clicked.connect(lambda: self.delete_section(section))
        self.sections_layout.addWidget(section)
        return section

    def add_experience_item(self, layout):
        group = QGroupBox("Job")
        form = QFormLayout(group)
        widgets = {'title': QLineEdit(), 'company': QLineEdit(), 'location': QLineEdit(), 'years': QLineEdit(), 'description': QTextEdit()}
        for key, widget in widgets.items():
            form.addRow(f"{key.title()}:", widget)
            widget.textChanged.connect(self.schedule_preview_update)
        ai_button = QPushButton("AI Suggestion for this Description")
        ai_button.clicked.connect(lambda ch, w=widgets, g=group: self.handle_targeted_ai_suggestion("experience_description", w['description'], g))
        form.addRow(ai_button)
        group.setProperty("widgets", widgets)
        layout.addWidget(group)

    def add_education_item(self, layout):
        group = QGroupBox("Degree")
        form = QFormLayout(group)
        widgets = {'degree': QLineEdit(), 'university': QLineEdit(), 'years': QLineEdit()}
        for key, widget in widgets.items():
            form.addRow(f"{key.title()}:", widget)
            widget.textChanged.connect(self.schedule_preview_update)
        group.setProperty("widgets", widgets)
        layout.addWidget(group)

    def move_section(self, section, direction):
        index = self.sections_layout.indexOf(section)
        new_index = index + direction
        if 0 <= new_index < self.sections_layout.count():
            self.sections_layout.removeWidget(section)
            self.sections_layout.insertWidget(new_index, section)
            self.schedule_preview_update()

    def delete_section(self, section):
        reply = QMessageBox.question(self, 'Delete Section', f"Are you sure you want to delete the '{section.title()}' section?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            section.deleteLater()
            self.schedule_preview_update()

    def gather_data(self):
        data = {'name': self.name_input.text(),'email': self.email_input.text(),'phone': self.phone_input.text(),'linkedin': self.linkedin_input.text(),'sections': []}
        for i in range(self.sections_layout.count()):
            section_widget = self.sections_layout.itemAt(i).widget()
            if not section_widget: continue
            sec_type = section_widget.section_type
            sec_title = section_widget.title()
            sec_data = {'type': sec_type, 'title': sec_title, 'content': None}
            if sec_type in ['summary', 'skills', 'custom']:
                content_widget = section_widget.findChild(QTextEdit)
                if content_widget: sec_data['content'] = content_widget.toPlainText()
            elif sec_type == 'experience':
                jobs = []
                job_groups = section_widget.findChildren(QGroupBox)
                for group in job_groups:
                    widgets = group.property("widgets")
                    if widgets: jobs.append({k: v.text() if isinstance(v, QLineEdit) else v.toPlainText() for k, v in widgets.items()})
                sec_data['content'] = jobs
            elif sec_type == 'education':
                degrees = []
                edu_groups = section_widget.findChildren(QGroupBox)
                for group in edu_groups:
                    widgets = group.property("widgets")
                    if widgets: degrees.append({k: v.text() for k, v in widgets.items()})
                sec_data['content'] = degrees
            data['sections'].append(sec_data)
        return data

    def add_custom_section_dialog(self):
        text, ok = QInputDialog.getText(self, "Add Custom Section", "Enter the title for the new section:")
        if ok and text:
            self.add_section("custom", text)
            self.schedule_preview_update()

    def set_api_key(self):
        text, ok = QInputDialog.getText(self, "API Key", "Paste your OpenRouter.ai API Key:")
        if ok and text: self.api_key = text
    
    def handle_targeted_ai_suggestion(self, field_type, target_widget, context_group=None):
        if not self.api_key or not self.job_role_input.text():
            QMessageBox.warning(self, "Input Missing", "Please set your API Key and a Target Job Title first.")
            return
        full_resume_data = self.gather_data()
        job_context = None
        if field_type == "experience_description" and context_group:
            widgets = context_group.property("widgets")
            job_context = {"title": widgets['title'].text(), "company": widgets['company'].text()}
        suggestion = get_targeted_ai_suggestion(self.api_key, self.job_role_input.text(), full_resume_data, field_type, job_context)
        if suggestion.startswith("Error:"):
            QMessageBox.critical(self, "AI Error", f"Could not get suggestion.\n\n{suggestion}")
        else:
            target_widget.setText(suggestion)