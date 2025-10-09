import os
import subprocess
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

logger = logging.getLogger()

def generate_latex_resume(data, template_name, is_preview=False):
    """
    Generates a PDF resume.
    If is_preview is True, it overwrites a single '_preview.pdf' file.
    If is_preview is False, it creates a new timestamped PDF file.
    """
    logger.info(f"Starting PDF generation (Preview: {is_preview}) with template: '{template_name}'.")
    try:
        template_dir = os.path.abspath('templates')
        output_dir = os.path.abspath('output')
            
        os.makedirs(output_dir, exist_ok=True)
        
        env = Environment(
            loader=FileSystemLoader(template_dir),
            block_start_string='\\block{',
            block_end_string='}',
            variable_start_string='{{',
            variable_end_string='}}',
            comment_start_string='\\#{',
            comment_end_string='}',
            line_statement_prefix='%%',
            line_comment_prefix='%#',
            trim_blocks=True,
            autoescape=False
        )

        template_path = f"{template_name}/template.tex"
        template = env.get_template(template_path)
        
        rendered_latex = template.render(data)
        
        # --- DYNAMIC FILENAME LOGIC ---
        if is_preview:
            base_filename = "_preview" # A consistent name for fast overwriting
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"resume_{timestamp}"
        # -------------------------------
        
        tex_filepath = os.path.join(output_dir, f"{base_filename}.tex")
        pdf_filepath = os.path.join(output_dir, f"{base_filename}.pdf")

        with open(tex_filepath, 'w', encoding='utf-8') as f:
            f.write(rendered_latex)
            
        # Run pdflatex only once for previews to make it faster
        compilation_runs = 1 if is_preview else 2
        for i in range(compilation_runs):
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', output_dir, tex_filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if process.returncode != 0:
                logger.error(f"LaTeX compilation failed on run {i + 1}.")
                logger.error(f"pdflatex error output:\n---BEGIN LATEX LOG---\n{process.stdout}\n---END LATEX LOG---")
                return None
        
        if os.path.exists(pdf_filepath):
            logger.info(f"PDF generated successfully at: {pdf_filepath}")
            return pdf_filepath
        else:
            logger.error("PDF file not found after successful compilation command.")
            return None

    except Exception as e:
        logger.error(f"An unexpected error occurred during PDF generation: {e}", exc_info=True)
        return None