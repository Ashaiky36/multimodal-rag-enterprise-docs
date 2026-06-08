"""
Export chat Q&A to PDF.
"""

from pathlib import Path
from datetime import datetime
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFExporter:
    """
    Export conversation history to PDF.
    """
    
    def __init__(self):
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required libraries are installed."""
        try:
            from fpdf import FPDF
            self.fpdf_available = True
        except ImportError:
            self.fpdf_available = False
            logger.warning("fpdf not installed. Run: pip install fpdf2")
    
    def export_conversation(self, messages: List[Dict], document_name: str, output_path: str) -> bool:
        """
        Export conversation to PDF.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            document_name: Name of the document being analyzed
            output_path: Path to save the PDF
        """
        if not self.fpdf_available:
            logger.error("fpdf2 not installed")
            return False
        
        try:
            from fpdf import FPDF
            
            class PDF(FPDF):
                def header(self):
                    self.set_font('Arial', 'B', 12)
                    self.cell(0, 10, 'Document Intelligence - Q&A Export', 0, 1, 'C')
                    self.ln(5)
                
                def footer(self):
                    self.set_y(-15)
                    self.set_font('Arial', 'I', 8)
                    self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
            
            pdf = PDF()
            pdf.add_page()
            
            # Title
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f'Document: {document_name}', 0, 1)
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(0, 10, f'Export Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
            pdf.ln(10)
            
            # Conversation
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                
                # Role label
                pdf.set_font('Arial', 'B', 11)
                pdf.set_text_color(79, 70, 229) if role == "user" else pdf.set_text_color(16, 185, 129)
                pdf.cell(0, 8, f"{'Q:' if role == 'user' else 'A:'}", 0, 1)
                
                # Content
                pdf.set_font('Arial', '', 10)
                pdf.set_text_color(0, 0, 0)
                
                # Handle multi-line content
                pdf.multi_cell(0, 6, content)
                pdf.ln(5)
                
                # Add sources if available
                if msg.get("sources"):
                    pdf.set_font('Arial', 'I', 8)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 5, f"Sources: {len(msg['sources'])} chunks retrieved", 0, 1)
                
                pdf.ln(3)
            
            # Save
            pdf.output(output_path)
            logger.info(f"PDF exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"PDF export failed: {e}")
            return False


def export_to_pdf(messages: List[Dict], document_name: str) -> Optional[bytes]:
    """
    Export conversation to PDF and return as bytes for download.
    """
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        
        # Header
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'Document: {document_name}', 0, 1)
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, f'Export: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
        pdf.ln(10)
        
        # Messages
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            pdf.set_font('Arial', 'B', 11)
            pdf.set_text_color(79, 70, 229) if role == "user" else pdf.set_text_color(16, 185, 129)
            pdf.cell(0, 8, f"{'QUESTION' if role == 'user' else 'ANSWER'}:", 0, 1)
            
            pdf.set_font('Arial', '', 10)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 6, content)
            pdf.ln(5)
        
        return pdf.output(dest='S').encode('latin1')
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return None