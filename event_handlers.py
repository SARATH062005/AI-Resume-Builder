import os
import time
import json
import re
import logging
from PyQt6.QtWidgets import QMessageBox, QInputDialog
from PyQt6.QtCore import QUrl

# Direct imports from sibling files
from latex_service import generate_latex_resume
from openrouter_service import get_targeted_ai_suggestion, get_ats_score_and_feedback
from ui_components import ATSResultsDialog
from data_handler import gather_data

logger = logging.getLogger()

class EventHandlers:
    def __init__(self, main_window):
        self.win = main_window

    # ... (ALL OTHER METHODS IN THIS CLASS ARE IDENTICAL TO THE PREVIOUS VERSION)
    # ... PASTE THE REST OF THE EventHandlers CLASS CODE HERE ...
    def schedule_preview_update(self, *args, **kwargs):
        # Accept arbitrary args so this can be connected directly to PyQt signals
        # like textChanged which may pass the new text.
        self.win.preview_timer.start()

    def update_live_preview(self):
        logger.info("User paused typing. Updating live preview...")
        resume_data = gather_data(self.win)
        template_name = self.win.template_combo.currentText()
        pdf_path = generate_latex_resume(resume_data, template_name, is_preview=True)
        if pdf_path:
            qurl = QUrl.fromLocalFile(os.path.abspath(pdf_path))
            qurl.setQuery(f"cache_buster={int(time.time())}")
            self.win.pdf_viewer.setUrl(qurl)
            self.win.right_tabs.setCurrentIndex(0)
        else:
            logger.error("Live preview update failed.")
    
    def save_final_pdf(self):
        logger.info("'Save Final PDF' button clicked.")
        resume_data = gather_data(self.win)
        template_name = self.win.template_combo.currentText()
        pdf_path = generate_latex_resume(resume_data, template_name, is_preview=False)
        if pdf_path:
            full_path = os.path.abspath(pdf_path)
            QMessageBox.information(self.win, "PDF Saved", f"Successfully saved the final resume to:\n{full_path}")
        else:
            QMessageBox.critical(self.win, "PDF Generation Failed", "Check 'Application Logs' for details.")
            self.win.right_tabs.setCurrentIndex(1)
            
    def set_api_key(self):
        text, ok = QInputDialog.getText(self.win, "API Key", "Paste your OpenRouter.ai API Key:")
        if ok and text: self.win.api_key = text

    def move_section(self, section, direction):
        index = self.win.sections_layout.indexOf(section)
        new_index = index + direction
        if 0 <= new_index < self.win.sections_layout.count():
            self.win.sections_layout.removeWidget(section)
            self.win.sections_layout.insertWidget(new_index, section)
            self.schedule_preview_update()

    def delete_section(self, section):
        reply = QMessageBox.question(self.win, 'Delete Section', f"Delete '{section.title()}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            section.deleteLater()
            self.schedule_preview_update()

    def handle_targeted_ai_suggestion(self, field_type, target_widget, context_group=None):
        if not self.win.api_key or not self.win.job_role_input.text():
            QMessageBox.warning(self.win, "Input Missing", "Please set API Key and Target Job Title.")
            return
        
        full_resume_data = gather_data(self.win)
        job_context = None
        if field_type == "experience_description" and context_group:
            widgets = context_group.property("widgets")
            job_context = {"title": widgets['title'].text(), "company": widgets['company'].text()}

        suggestion = get_targeted_ai_suggestion(self.win.api_key, self.win.job_role_input.text(), full_resume_data, field_type, job_context)

        if suggestion.startswith("Error:"):
            QMessageBox.critical(self.win, "AI Error", f"Could not get suggestion.\n\n{suggestion}")
        else:
            target_widget.setText(suggestion)
            QMessageBox.information(self.win, "Success", "AI suggestion applied.")

    def handle_ats_check(self):
        logger.info("'Check ATS Score' button clicked.")
        if not self.win.api_key:
            QMessageBox.warning(self.win, "API Key Missing", "Please set your OpenRouter API key first.")
            return
        job_description = self.win.job_description_input.toPlainText()
        if not job_description:
            QMessageBox.warning(self.win, "Input Missing", "Please paste the target job description.")
            return
            
        resume_data = gather_data(self.win)
        QMessageBox.information(self.win, "AI Request", "Analyzing resume... This may take a moment.")
        
        response_raw = get_ats_score_and_feedback(self.win.api_key, job_description, resume_data)
        
        try:
            match = re.search(r'\{.*\}', response_raw, re.DOTALL)
            if not match: raise json.JSONDecodeError("No JSON object found.", response_raw, 0)
            data = json.loads(match.group(0))
            if "error" in data: raise Exception(data["error"])
            dialog = ATSResultsDialog(data, self.win)
            dialog.exec()
        except Exception as e:
            logger.error(f"Failed to parse ATS response: {e}\nRaw response:\n{response_raw}")
            QMessageBox.critical(self.win, "AI Error", "Could not parse the AI's response. Check logs.")
            self.win.right_tabs.setCurrentIndex(1)