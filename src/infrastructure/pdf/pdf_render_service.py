"""PDF rendering service - converts HTML to PDF"""
import base64
from typing import Optional
from weasyprint import HTML

class PdfRenderService:
    """Service for rendering PDF documents from HTML"""
    
    @staticmethod
    def render_to_bytes(html_content: str, base_url: Optional[str] = None) -> bytes:
        """
        Convert HTML string to PDF bytes.
        
        Args:
            html_content: HTML string to render
            base_url: Optional base URL for resolving relative paths (images, CSS)
            
        Returns:
            PDF as bytes
        """
        doc = HTML(string=html_content, base_url=base_url)

        return doc.write_pdf()

    @staticmethod
    def render_to_base64(html_content: str, base_url: Optional[str] = None) -> str:
        """Convert HTML string to base64-encoded PDF string."""
        pdf_bytes = PdfRenderService.render_to_bytes(html_content, base_url)

        return base64.b64encode(pdf_bytes).decode('utf-8')
