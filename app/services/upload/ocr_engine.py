"""
OCR Engine using PaddleOCR
Multilingual text extraction from images
Supports English, Hindi, Chinese, Arabic, and 80+ languages
"""
import os
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

from app.utils import logger, ExtractionError


class OCREngine:
    """OCR Engine - Singleton for efficient model loading"""
    
    _instance = None
    _ocr = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self, language: str = "en"):
        """
        Lazy load OCR model (downloaded on first use ~100MB).
        
        Args:
            language: 'en', 'ch', 'hi', 'ar', etc. or 'multi' for multilingual
        """
        if self._ocr is None:
            logger.info(f"Loading PaddleOCR model (language: {language})...")
            logger.info("First run will download ~100MB, please wait...")
            
            try:
                from paddleocr import PaddleOCR
                
                # Initialize with optimal settings
                self._ocr = PaddleOCR(
                    use_angle_cls=True,      # Detect rotated text
                    lang=language,            # Language
                    use_gpu=False,            # CPU mode (change to True if GPU available)
                    show_log=False,           # Reduce verbosity
                    use_space_char=True,      # Preserve spaces
                    drop_score=0.5            # Minimum confidence
                )
                
                logger.info("PaddleOCR model loaded successfully!")
            except Exception as e:
                logger.error(f"Failed to load OCR model: {e}")
                raise ExtractionError("OCR", f"Model loading failed: {e}")
        
        return self._ocr
    
    def extract_from_image(
        self,
        image_input,
        preprocess: bool = True,
        language: str = "en"
    ) -> Dict:
        """
        Extract text from image (file path or numpy array).
        
        Args:
            image_input: File path (str) or numpy array
            preprocess: Apply image preprocessing
            language: OCR language
            
        Returns:
            {
                'full_text': str,
                'lines': [{'text': str, 'confidence': float, 'bbox': [...]}],
                'total_lines': int,
                'avg_confidence': float,
                'word_count': int
            }
        """
        try:
            ocr = self.load_model(language)
            
            # Preprocess if file path provided
            if isinstance(image_input, str):
                logger.info(f"OCR processing: {Path(image_input).name}")
                
                if preprocess:
                    from app.services.upload.image_preprocessor import image_preprocessor
                    image = image_preprocessor.preprocess(image_input)
                    image = image_preprocessor.resize_for_ocr(image)
                else:
                    import cv2
                    image = cv2.imread(image_input)
            else:
                # Already numpy array
                image = image_input
            
            # Run OCR
            result = ocr.ocr(image, cls=True)
            
            if not result or not result[0]:
                logger.warning("No text detected in image")
                return self._empty_result()
            
            # Parse results
            lines = []
            full_text_parts = []
            confidences = []
            
            for detection in result[0]:
                if not detection or len(detection) < 2:
                    continue
                
                bbox = detection[0]      # Bounding box coordinates
                text_data = detection[1]  # (text, confidence)
                
                if isinstance(text_data, tuple) and len(text_data) >= 2:
                    text, confidence = text_data[0], text_data[1]
                    
                    if text and text.strip():
                        lines.append({
                            'text': text.strip(),
                            'confidence': round(float(confidence), 4),
                            'bbox': [[float(p[0]), float(p[1])] for p in bbox]
                        })
                        full_text_parts.append(text.strip())
                        confidences.append(float(confidence))
            
            # Build result
            full_text = "\n".join(full_text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            result_dict = {
                'full_text': full_text,
                'lines': lines,
                'total_lines': len(lines),
                'avg_confidence': round(avg_confidence, 4),
                'word_count': len(full_text.split()),
                'language': language
            }
            
            logger.info(
                f"OCR extracted: {result_dict['total_lines']} lines, "
                f"{result_dict['word_count']} words, "
                f"confidence: {avg_confidence:.2%}"
            )
            
            return result_dict
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise ExtractionError("OCR", str(e))
    
    def extract_from_pdf_page(self, image_array: np.ndarray, language: str = "en") -> str:
        """Quick OCR for PDF page (returns just text)"""
        try:
            result = self.extract_from_image(image_array, preprocess=True, language=language)
            return result['full_text']
        except Exception as e:
            logger.warning(f"PDF page OCR failed: {e}")
            return ""
    
    def _empty_result(self) -> Dict:
        """Return empty result structure"""
        return {
            'full_text': '',
            'lines': [],
            'total_lines': 0,
            'avg_confidence': 0.0,
            'word_count': 0,
            'language': 'unknown'
        }
    
    def detect_language(self, image_path: str) -> str:
        """
        Auto-detect language in image.
        For now, defaults to English. Can be enhanced with langdetect.
        """
        # Simple heuristic - try English first
        # Can be enhanced to test multiple languages
        return "en"


# Global instance
ocr_engine = OCREngine()
