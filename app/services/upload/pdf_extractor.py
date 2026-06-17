"""
PDF Text Extraction Service using PyMuPDF
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict
from loguru import logger


class PDFExtractor:
    """Extract text from PDF files page by page"""
    
    def extract_text(self, file_path: str) -> Dict:
        """
        Extract all text from PDF
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            {
                'total_pages': int,
                'full_text': str,
                'pages': [{'page_number': int, 'text': str}],
                'metadata': dict
            }
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")
        
        if not path.suffix.lower() == '.pdf':
            raise ValueError(f"Not a PDF file: {file_path}")
        
        logger.info(f"Extracting text from: {path.name}")
        
        try:
            doc = fitz.open(file_path)
            
            pages = []
            full_text_parts = []
            
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text")
                
                if text.strip():
                    pages.append({
                        'page_number': page_num,
                        'text': text.strip(),
                        'char_count': len(text)
                    })
                    full_text_parts.append(text.strip())
            
            metadata = {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creator': doc.metadata.get('creator', '')
            }
            
            result = {
                'total_pages': len(doc),
                'pages_with_text': len(pages),
                'full_text': '\n\n'.join(full_text_parts),
                'pages': pages,
                'metadata': metadata,
                'total_characters': sum(p['char_count'] for p in pages)
            }
            
            doc.close()
            
            logger.info(
                f"Extracted {result['pages_with_text']}/{result['total_pages']} pages, "
                f"{result['total_characters']} characters"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise
    
    def extract_text_only(self, file_path: str) -> str:
        """Quick method: just get all text as single string"""
        result = self.extract_text(file_path)
        return result['full_text']


# Global instance
pdf_extractor = PDFExtractor()
