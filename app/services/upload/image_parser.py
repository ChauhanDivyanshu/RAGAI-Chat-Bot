"""
Image Parser - Extract text from images using OCR
Supports JPG, JPEG, PNG
"""
from pathlib import Path
from typing import Dict, Optional
from PIL import Image

from app.utils import logger, ExtractionError


class ImageParser:
    """Parse images using OCR"""
    
    def extract(self, file_path: str, language: str = "en") -> Dict:
        """
        Extract text from image file.
        
        Args:
            file_path: Path to image
            language: OCR language (default: English)
            
        Returns:
            Standardized extraction result
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {file_path}")
        
        logger.info(f"Extracting text from image: {path.name}")
        
        try:
            # Get image info
            img = Image.open(file_path)
            width, height = img.size
            mode = img.mode
            format_name = img.format
            img.close()
            
            # Run OCR
            from app.services.upload.ocr_engine import ocr_engine
            
            ocr_result = ocr_engine.extract_from_image(
                image_input=file_path,
                preprocess=True,
                language=language
            )
            
            full_text = ocr_result['full_text']
            
            if not full_text or len(full_text.strip()) < 5:
                logger.warning(f"Very little text extracted from image")
            
            result = {
                'full_text': full_text,
                'pages': [{
                    'page_number': 1,
                    'text': full_text,
                    'char_count': len(full_text)
                }],
                'total_pages': 1,
                'total_characters': len(full_text),
                'metadata': {
                    'image_format': format_name,
                    'image_mode': mode,
                    'image_size': f"{width}x{height}",
                    'ocr_language': language,
                    'ocr_confidence': ocr_result['avg_confidence'],
                    'lines_detected': ocr_result['total_lines']
                },
                'extraction_type': 'image_ocr',
                'has_pages': False,
                'ocr_stats': {
                    'total_lines': ocr_result['total_lines'],
                    'word_count': ocr_result['word_count'],
                    'confidence': ocr_result['avg_confidence']
                }
            }
            
            logger.info(
                f"Image OCR complete: {ocr_result['word_count']} words, "
                f"confidence: {ocr_result['avg_confidence']:.2%}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            raise ExtractionError("Image", str(e))


# Global instance
image_parser = ImageParser()
