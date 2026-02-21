"""Module that generates the PDF report based on provided HTML file"""

import io
import os
from io import BytesIO

import weasyprint

from src.utils.logger import setup_logger

report = [
    {"name": "Similar-c19d2ac0", "total": 1, "days": ["Fri"], "status": "Active"},
    {"name": "Young-bed71ced", "total": 1, "days": ["Fri"], "status": "Active"},
    {"name": "On-74fd00ff", "total": 1, "days": ["Fri"], "status": "Active"},
    {"name": "Much-f5fc3480", "total": 1, "days": ["Fri"], "status": "Active"},
    {"name": "Clear-6b886562", "total": 1, "days": ["Fri"], "status": "Active"},
]

BASE_DIR = os.path.abspath(__file__)
PDFS_DIR = os.path.join(BASE_DIR, "../../pdfs")
logger = setup_logger(__name__)


class PDFGenerator:
    """Class used for generating the PDF reports"""

    @staticmethod
    def generate_pdf_report_to_hard_drive(html_report_file: str, pdf_name: str) -> None:
        """Generates and saves a PDF report on the hard drive"""
        try:
            weasyprint.HTML(filename=html_report_file).write_pdf(os.path.join(PDFS_DIR, pdf_name))
        except OSError as e:
            logger.error(f"Error during generating the PDF file: {e}")

    @staticmethod
    def create_pdf_buffer(html_string: str) -> BytesIO:
        """Writes a HTML report file to in-memory IO buffer"""
        try:
            buffer = io.BytesIO()
            weasyprint.HTML(string=html_string).write_pdf(buffer)
            return buffer
        except OSError as e:
            logger.error(f"Error during saving HTML file to a bufer: {e}")
            raise
