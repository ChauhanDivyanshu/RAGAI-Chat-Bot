"""
Universal Document Processor
Routes documents to appropriate parser based on file type
"""
from typing import Dict
from pathlib import Path

from app.utils import logger, ExtractionError
from app.services.upload.file_detector import file_detector


class DocumentProcessor:
    """Universal document processing pipeline"""
    
    def __init__(self):
        self._pdf_parser = None
        self._docx_parser = None
        self._excel_parser = None
        self._html_parser = None
        self._image_parser = None
    
    @property
    def pdf_parser(self):
        if self._pdf_parser is None:
            from app.services.upload.pdf_extractor import pdf_extractor
            self._pdf_parser = pdf_extractor
        return self._pdf_parser
    
    @property
    def docx_parser(self):
        if self._docx_parser is None:
            from app.services.upload.docx_parser import docx_parser
            self._docx_parser = docx_parser
        return self._docx_parser
    
    @property
    def excel_parser(self):
        if self._excel_parser is None:
            from app.services.upload.excel_parser import excel_parser
            self._excel_parser = excel_parser
        return self._excel_parser
    
    @property
    def html_parser(self):
        if self._html_parser is None:
            from app.services.upload.html_parser import html_parser
            self._html_parser = html_parser
        return self._html_parser
    
    @property
    def image_parser(self):
        if self._image_parser is None:
            from app.services.upload.image_parser import image_parser
            self._image_parser = image_parser
        return self._image_parser
    
    def process(self, file_path: str, file_type: str, language: str = "en") -> Dict:
        """Process any supported document type"""
        logger.info(f"Processing {file_type} file: {Path(file_path).name}")
        
        try:
            if file_type == "pdf":
                result = self.pdf_parser.extract_text(file_path, ocr_language=language)
                return self._standardize_pdf_result(result)
            
            elif file_type in ("docx", "doc"):
                result = self.docx_parser.extract(file_path)
                return self._standardize_docx_result(result)
            
            elif file_type in ("xlsx", "xls", "csv"):
                result = self.excel_parser.extract(file_path, file_type)
                return self._standardize_excel_result(result)
            
            elif file_type in ("html", "htm", "txt", "md"):
                result = self.html_parser.extract(file_path, file_type)
                return self._standardize_text_result(result)
            
            elif file_type in ("jpg", "jpeg", "png"):
                result = self.image_parser.extract(file_path, language)
                return result  # Already standardized
            
            else:
                raise ExtractionError(file_type, f"No parser available for {file_type}")
                
        except ExtractionError:
            raise
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise ExtractionError(file_type, str(e))
    
    def _standardize_pdf_result(self, result: Dict) -> Dict:
        return {
            'full_text': result['full_text'],
            'pages': result.get('pages', []),
            'total_pages': result.get('total_pages', 0),
            'total_characters': result.get('total_characters', 0),
            'metadata': result.get('metadata', {}),
            'extraction_type': result.get('extraction_type', 'pdf'),
            'has_pages': True,
            'pdf_classification': result.get('pdf_classification', 'text')
        }
    
    def _standardize_docx_result(self, result: Dict) -> Dict:
        full_text = result['full_text']
        pages = [{
            'page_number': 1,
            'text': full_text,
            'char_count': len(full_text)
        }]
        return {
            'full_text': full_text,
            'pages': pages,
            'total_pages': 1,
            'total_characters': result['stats']['total_characters'],
            'metadata': result.get('metadata', {}),
            'extraction_type': 'docx',
            'has_pages': False,
            'tables_count': result['stats'].get('tables_count', 0),
            'headings_count': result['stats'].get('headings_count', 0)
        }
    
    def _standardize_excel_result(self, result: Dict) -> Dict:
        full_text = result['full_text']
        pages = []
        for i, sheet in enumerate(result['sheets'], 1):
            pages.append({
                'page_number': i,
                'sheet_name': sheet['name'],
                'text': sheet['text'],
                'char_count': len(sheet['text'])
            })
        return {
            'full_text': full_text,
            'pages': pages,
            'total_pages': result['stats']['sheets_count'],
            'total_characters': result['stats']['total_characters'],
            'metadata': result.get('metadata', {}),
            'extraction_type': 'spreadsheet',
            'has_pages': False,
            'sheets_count': result['stats']['sheets_count'],
            'total_rows': result['stats']['total_rows']
        }
    
    def _standardize_text_result(self, result: Dict) -> Dict:
        full_text = result['full_text']
        pages = [{
            'page_number': 1,
            'text': full_text,
            'char_count': len(full_text)
        }]
        return {
            'full_text': full_text,
            'pages': pages,
            'total_pages': 1,
            'total_characters': result['stats']['total_characters'],
            'metadata': result.get('metadata', {}),
            'extraction_type': 'text',
            'has_pages': False
        }


# Global instance
document_processor = DocumentProcessor()
