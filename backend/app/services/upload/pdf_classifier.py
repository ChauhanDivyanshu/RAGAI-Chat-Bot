"""
PDF Classifier
Determines if PDF is text-based, scanned, or hybrid
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List

from app.utils import logger


class PDFClassifier:
    """Classify PDF type for optimal extraction strategy"""
    
    # Thresholds
    MIN_TEXT_PER_PAGE = 50  # chars
    MIN_TEXT_RATIO = 0.7    # 70% pages must have text
    
    def classify(self, file_path: str) -> Dict:
        """
        Analyze PDF and classify its type.
        
        Returns:
            {
                'type': 'text' | 'scanned' | 'hybrid',
                'total_pages': int,
                'text_pages': int,
                'scanned_pages': int,
                'page_classifications': [...],
                'recommended_strategy': 'pdf_extract' | 'ocr' | 'hybrid',
                'has_images': bool,
                'avg_text_per_page': float
            }
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")
        
        logger.info(f"Classifying PDF: {path.name}")
        
        try:
            doc = fitz.open(file_path)
            total_pages = len(doc)
            
            page_data = []
            total_text_chars = 0
            text_pages = 0
            scanned_pages = 0
            has_images = False
            
            for page_num, page in enumerate(doc, start=1):
                # Get text
                text = page.get_text("text").strip()
                text_length = len(text)
                total_text_chars += text_length
                
                # Get images on page
                images = page.get_images()
                page_has_images = len(images) > 0
                if page_has_images:
                    has_images = True
                
                # Classify page
                if text_length >= self.MIN_TEXT_PER_PAGE:
                    page_type = "text"
                    text_pages += 1
                elif page_has_images and text_length < 20:
                    page_type = "scanned"
                    scanned_pages += 1
                else:
                    page_type = "mixed"
                
                page_data.append({
                    'page_number': page_num,
                    'type': page_type,
                    'text_length': text_length,
                    'image_count': len(images),
                    'preview': text[:100] if text else None
                })
            
            doc.close()
            
            # Determine overall type
            text_ratio = text_pages / total_pages if total_pages > 0 else 0
            scanned_ratio = scanned_pages / total_pages if total_pages > 0 else 0
            
            if text_ratio >= self.MIN_TEXT_RATIO:
                pdf_type = "text"
                strategy = "pdf_extract"
            elif scanned_ratio >= self.MIN_TEXT_RATIO:
                pdf_type = "scanned"
                strategy = "ocr"
            else:
                pdf_type = "hybrid"
                strategy = "hybrid"
            
            avg_text_per_page = total_text_chars / total_pages if total_pages > 0 else 0
            
            result = {
                'type': pdf_type,
                'total_pages': total_pages,
                'text_pages': text_pages,
                'scanned_pages': scanned_pages,
                'page_classifications': page_data,
                'recommended_strategy': strategy,
                'has_images': has_images,
                'avg_text_per_page': round(avg_text_per_page, 2),
                'text_ratio': round(text_ratio, 4)
            }
            
            logger.info(
                f"PDF classified as: {pdf_type.upper()} "
                f"({text_pages} text + {scanned_pages} scanned of {total_pages} pages)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"PDF classification failed: {e}")
            # Default to text extraction if classification fails
            return {
                'type': 'text',
                'total_pages': 0,
                'text_pages': 0,
                'scanned_pages': 0,
                'page_classifications': [],
                'recommended_strategy': 'pdf_extract',
                'has_images': False,
                'avg_text_per_page': 0,
                'text_ratio': 1.0
            }


# Global instance
pdf_classifier = PDFClassifier()
