import logging
from PyQt6.QtWidgets import QLineEdit, QTextEdit, QGroupBox

logger = logging.getLogger(__name__)

def gather_data(main_window):
    """
    Gathers all data from the UI in visual order and structures it
    for backend services (LaTeX rendering, AI suggestions, etc.)
    """

    data = {
        'name': main_window.name_input.text().strip(),
        'email': main_window.email_input.text().strip(),
        'phone': main_window.phone_input.text().strip(),
        'linkedin': main_window.linkedin_input.text().strip(),
        'sections': []
    }

    layout = main_window.sections_layout
    total_sections = layout.count()
    logger.debug(f"Gathering data from {total_sections} sections...")

    for i in range(total_sections):
        section_widget = layout.itemAt(i).widget()
        if not section_widget:
            continue

        sec_type = getattr(section_widget, 'section_type', None)
        sec_title = getattr(section_widget, 'title', lambda: "Untitled")()
        sec_data = {'type': sec_type, 'title': sec_title, 'content': None}

        # --- Handle simple text-based sections ---
        if sec_type in ['summary', 'skills', 'custom', 'custom_textarea']:
            content_widget = section_widget.findChild(QTextEdit)
            if content_widget:
                text = content_widget.toPlainText().strip()
                sec_data['content'] = text if text else ""
                logger.debug(f"Collected text for section [{sec_title}]")

        # --- Handle experience section (multiple jobs) ---
        elif sec_type == 'experience':
            jobs = []
            for group in section_widget.findChildren(QGroupBox):
                widgets = group.property("widgets")
                if not widgets:
                    continue
                job_entry = {
                    key: w.toPlainText().strip() if isinstance(w, QTextEdit) else w.text().strip()
                    for key, w in widgets.items()
                }
                jobs.append(job_entry)
            sec_data['content'] = jobs
            logger.debug(f"Collected {len(jobs)} job entries from [{sec_title}]")

        # --- Handle education section (multiple degrees) ---
        elif sec_type == 'education':
            degrees = []
            for group in section_widget.findChildren(QGroupBox):
                widgets = group.property("widgets")
                if not widgets:
                    continue
                degree_entry = {key: w.text().strip() for key, w in widgets.items()}
                degrees.append(degree_entry)
            sec_data['content'] = degrees
            logger.debug(f"Collected {len(degrees)} education entries from [{sec_title}]")

        # --- Handle custom field-based sections (structured data) ---
        elif sec_type == 'custom_fields':
            items = []
            for group in section_widget.findChildren(QGroupBox):
                widgets = group.property("widgets")
                if not widgets:
                    continue
                item_entry = {key: w.text().strip() for key, w in widgets.items()}
                items.append(item_entry)
            sec_data['content'] = items
            logger.debug(f"Collected {len(items)} custom field entries from [{sec_title}]")

        # --- Fallback for unknown sections ---
        else:
            # Try to detect if there's a QTextEdit or QLineEdit anyway
            text_widget = section_widget.findChild(QTextEdit) or section_widget.findChild(QLineEdit)
            if text_widget:
                sec_data['content'] = text_widget.toPlainText().strip() if isinstance(text_widget, QTextEdit) else text_widget.text().strip()
                logger.warning(f"Handled unknown section [{sec_title}] of type '{sec_type}' as text content.")
            else:
                logger.warning(f"Skipped section [{sec_title}] (unrecognized type: {sec_type})")

        data['sections'].append(sec_data)

    logger.info(f"Successfully gathered {len(data['sections'])} sections from UI.")
    return data
