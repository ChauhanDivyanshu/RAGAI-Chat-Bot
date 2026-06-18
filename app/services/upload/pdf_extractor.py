"""
Enhanced PDF Extractor with OCR Support
Handles text-based, scanned, and hybrid PDFs
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, List
import numpy as np

from app.utils import logger, ExtractionError


class PDFExtractor:
    """Smart PDF extraction with OCR fallback for scanned PDFs"""
    
    def extract_text(
        self,
        file_path: str,
        use_ocr_fallback: bool = True,
        ocr_language: str = "en"
    ) -> Dict:
        """
        Extract text from PDF with smart strategy.
        
        Strategy:
        1. Classify PDF type
        2. For text PDFs: use PyMuPDF text extraction
        3. For scanned PDFs: use OCR
        4. For hybrid PDFs: use both
        
        Args:
            file_path: Path to PDF
            use_ocr_fallback: Use OCR if no text extracted
            ocr_language: OCR language
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {file_path}")
        
        logger.info(f"Extracting PDF: {path.name}")
        
        # Step 1: Classify PDF
        from app.services.upload.pdf_classifier import pdf_classifier
        classification = pdf_classifier.classify(file_path)
        
        pdf_type = classification['type']
        strategy = classification['recommended_strategy']
        
        logger.info(f"PDF type: {pdf_type}, strategy: {strategy}")
        
        try:
            if strategy == "pdf_extract":
                return self._extract_text_pdf(file_path, classification)
            elif strategy == "ocr":
                return self._extract_scanned_pdf(file_path, classification, ocr_language)
            else:  # hybrid
                return self._extract_hybrid_pdf(file_path, classification, ocr_language)
                
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise ExtractionError("PDF", str(e))
    
    def _extract_text_pdf(self, file_path: str, classification: Dict) -> Dict:
        """Standard text PDF extraction (fast)"""
        doc = fitz.open(file_path)
        
        pages = []
        full_text_parts = []
        
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            
            if text:
                pages.append({
                    'page_number': page_num,
                    'text': text,
                    'char_count': len(text),
                    'extraction_method': 'text'
                })
                full_text_parts.append(text)
        
        metadata = self._get_metadata(doc)
        doc.close()
        
        full_text = '\n\n'.join(full_text_parts)
        
        return {
            'full_text': full_text,
            'pages': pages,
            'total_pages': classification['total_pages'],
            'pages_with_text': len(pages),
            'total_characters': len(full_text),
            'metadata': metadata,
            'extraction_type': 'pdf_text',
            'has_pages': True,
            'pdf_classification': classification['type']
        }
    
    def _extract_scanned_pdf(
        self,
        file_path: str,
        classification: Dict,
        language: str = "en"
    ) -> Dict:
        """Extract text from scanned PDF using OCR"""
        logger.info("Using OCR for scanned PDF (this may take time...)")
        
        try:
            from pdf2image import convert_from_path
            from app.services.upload.ocr_engine import ocr_engine
        except ImportError as e:
            logger.error(f"Required packages not installed: {e}")
            raise ExtractionError("PDF", "OCR dependencies missing")
        
        # Convert PDF pages to images
        logger.info("Converting PDF pages to images...")
        try:
            images = convert_from_path(file_path, dpi=200)
        except Exception as e:
            logger.error(f"PDF to image conversion failed: {e}")
            raise ExtractionError("PDF", f"Could not convert pages: {e}")
        
        pages = []
        full_text_parts = []
        
        for page_num, pil_image in enumerate(images, start=1):
            logger.info(f"OCR on page {page_num}/{len(images)}...")
            
            # Convert PIL to numpy array
            img_array = np.array(pil_image)
            
            # Run OCR
            ocr_text = ocr_engine.extract_from_pdf_page(img_array, language)
            
            if ocr_text:
                pages.append({
                    'page_number': page_num,
                    'text': ocr_text,
                    'char_count': len(ocr_text),
                    'extraction_method': 'ocr'
                })
                full_text_parts.append(ocr_text)
        
        full_text = '\n\n'.join(full_text_parts)
        
        # Get metadata
        doc = fitz.open(file_path)
        metadata = self._get_metadata(doc)
        doc.close()
        
        return {
            'full_text': full_text,
            'pages': pages,
            'total_pages': classification['total_pages'],
            'pages_with_text': len(pages),
            'total_characters': len(full_text),
            'metadata': metadata,
            'extraction_type': 'pdf_ocr',
            'has_pages': True,
            'pdf_classification': classification['type'],
            'ocr_language': language
        }
    
    def _extract_hybrid_pdf(
        self,
        file_path: str,
        classification: Dict,
        language: str = "en"
    ) -> Dict:
        """Mixed extraction - text where available, OCR where needed"""
        logger.info("Using hybrid extraction (text + OCR)")
        
        doc = fitz.open(file_path)
        
        try:
            from pdf2image import convert_from_path
            from app.services.upload.ocr_engine import ocr_engine
        except ImportError:
            logger.warning("OCR not available, falling back to text-only")
            return self._extract_text_pdf(file_path, classification)
        
        pages = []
        full_text_parts = []
        page_classifications = {p['page_number']: p['type'] for p in classification['page_classifications']}
        
        # Convert all pages to images upfront for scanned pages
        images = None
        
        for page_num, page in enumerate(doc, start=1):
            page_type = page_classifications.get(page_num, 'text')
            
            if page_type == 'text':
                # Use text extraction
                text = page.get_text("text").strip()
                method = 'text'
            else:
                # Use OCR
                if images is None:
                    logger.info("Converting PDF to images for OCR...")
                    images = convert_from_path(file_path, dpi=200)
                
                if page_num <= len(images):
                    img_array = np.array(images[page_num - 1])
                    text = ocr_engine.extract_from_pdf_page(img_array, language)
                    method = 'ocr'
                else:
                    text = ""
                    method = 'failed'
            
            if text:
                pages.append({
                    'page_number': page_num,
                    'text': text,
                    'char_count': len(text),
                    'extraction_method': method
                })
                full_text_parts.append(text)
        
        metadata = self._get_metadata(doc)
        doc.close()
        
        full_text = '\n\n'.join(full_text_parts)
        
        return {
            'full_text': full_text,
            'pages': pages,
            'total_pages': classification['total_pages'],
            'pages_with_text': len(pages),
            'total_characters': len(full_text),
            'metadata': metadata,
            'extraction_type': 'pdf_hybrid',
            'has_pages': True,
            'pdf_classification': classification['type'],
            'ocr_language': language
        }
    
    def _get_metadata(self, doc) -> Dict:
        """Extract PDF metadata"""
        try:
            return {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creator': doc.metadata.get('creator', ''),
                'producer': doc.metadata.get('producer', '')
            }
        except Exception:
            return {}
    
    def extract_text_only(self, file_path: str) -> str:
        """Quick method: just get all text"""
        result = self.extract_text(file_path)
        return result['full_text']


# Global instance
pdf_extractor = PDFExtractor()
