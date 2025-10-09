import logging
from PyQt6.QtWidgets import QLineEdit, QTextEdit, QGroupBox

logger = logging.getLogger()

def gather_data(main_window):
    """
    Gathers all data from the UI forms in their current visual order
    and structures it for the backend services.
    """
    # 1. Gather fixed personal data
    data = {
        'name': main_window.name_input.text(),
        'email': main_window.email_input.text(),
        'phone': main_window.phone_input.text(),
        'linkedin': main_window.linkedin_input.text(),
        'sections': []  # This list will hold all the dynamic sections in order
    }
    
    # 2. Iterate through the dynamic section widgets in the layout
    layout = main_window.sections_layout
    for i in range(layout.count()):
        section_widget = layout.itemAt(i).widget()
        if not section_widget:
            continue
        
        sec_type = section_widget.section_type
        sec_title = section_widget.title()
        sec_data = {'type': sec_type, 'title': sec_title, 'content': None}

        # 3. Extract content based on the section's type
        if sec_type in ['summary', 'skills', 'custom']:
            # These sections have one simple QTextEdit
            content_widget = section_widget.findChild(QTextEdit)
            if content_widget:
                sec_data['content'] = content_widget.toPlainText()

        elif sec_type == 'experience':
            # This section can have multiple "Job" QGroupBoxes
            jobs = []
            job_groups = section_widget.findChildren(QGroupBox)
            for group in job_groups:
                widgets = group.property("widgets")
                if widgets:
                    job_data = {
                        'title': widgets['title'].text(),
                        'company': widgets['company'].text(),
                        'location': widgets['location'].text(),
                        'years': widgets['years'].text(),
                        'description': widgets['description'].toPlainText()
                    }
                    jobs.append(job_data)
            sec_data['content'] = jobs

        elif sec_type == 'education':
            # This section can have multiple "Degree" QGroupBoxes
            degrees = []
            edu_groups = section_widget.findChildren(QGroupBox)
            for group in edu_groups:
                widgets = group.property("widgets")
                if widgets:
                    degree_data = {
                        'degree': widgets['degree'].text(),
                        'university': widgets['university'].text(),
                        'years': widgets['years'].text()
                    }
                    degrees.append(degree_data)
            sec_data['content'] = degrees

        data['sections'].append(sec_data)
    
    logger.info("Successfully gathered all data from UI forms in dynamic order.")
    return data