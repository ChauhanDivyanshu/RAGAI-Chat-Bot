"""
Image Preprocessor for OCR
Uses OpenCV to enhance images before text extraction
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import io

from app.utils import logger


class ImagePreprocessor:
    """Enhance images for better OCR accuracy"""
    
    def preprocess(
        self,
        image_path: str,
        save_processed: bool = False
    ) -> np.ndarray:
        """
        Full preprocessing pipeline.
        
        Steps:
        1. Load image
        2. Convert to grayscale
        3. Denoise
        4. Deskew (correct rotation)
        5. Enhance contrast
        6. Binarize (black & white)
        
        Returns:
            Processed image as numpy array
        """
        logger.info(f"Preprocessing image: {Path(image_path).name}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            # Try with PIL for problematic formats
            pil_img = Image.open(image_path)
            image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Step 1: Grayscale
        gray = self.to_grayscale(image)
        
        # Step 2: Denoise
        denoised = self.denoise(gray)
        
        # Step 3: Deskew
        deskewed = self.deskew(denoised)
        
        # Step 4: Enhance contrast
        enhanced = self.enhance_contrast(deskewed)
        
        # Step 5: Binarize (optional, sometimes hurts OCR)
        # binary = self.binarize(enhanced)
        
        if save_processed:
            output_path = str(Path(image_path).parent / f"processed_{Path(image_path).name}")
            cv2.imwrite(output_path, enhanced)
            logger.info(f"Saved processed image: {output_path}")
        
        return enhanced
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert to grayscale"""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    def denoise(self, image: np.ndarray) -> np.ndarray:
        """Remove noise from image"""
        # Non-local means denoising (best quality)
        return cv2.fastNlMeansDenoising(image, h=10, templateWindowSize=7, searchWindowSize=21)
    
    def deskew(self, image: np.ndarray, max_angle: float = 15.0) -> np.ndarray:
        """
        Detect and correct image rotation/skew.
        Useful for scanned documents that aren't perfectly aligned.
        """
        try:
            # Threshold to get binary image
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Find all non-zero pixels (text)
            coords = np.column_stack(np.where(binary > 0))
            
            if len(coords) < 100:
                return image
            
            # Get minimum rotated rectangle
            angle = cv2.minAreaRect(coords)[-1]
            
            # Adjust angle
            if angle < -45:
                angle = 90 + angle
            
            # Only rotate if significantly skewed
            if abs(angle) > max_angle or abs(angle) < 0.5:
                return image
            
            # Rotate
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(
                image, M, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            logger.debug(f"Deskewed image by {angle:.2f} degrees")
            return rotated
            
        except Exception as e:
            logger.warning(f"Deskew failed: {e}")
            return image
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Improve contrast using CLAHE"""
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(image)
    
    def binarize(self, image: np.ndarray) -> np.ndarray:
        """Convert to pure black & white using adaptive thresholding"""
        return cv2.adaptiveThreshold(
            image, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2
        )
    
    def resize_for_ocr(self, image: np.ndarray, target_dpi: int = 300) -> np.ndarray:
        """Resize image to optimal DPI for OCR (300 DPI is ideal)"""
        height, width = image.shape[:2]
        
        # If image is too small, upscale
        min_dimension = 1000
        if height < min_dimension or width < min_dimension:
            scale = min_dimension / min(height, width)
            new_height = int(height * scale)
            new_width = int(width * scale)
            return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # If too large, downscale
        max_dimension = 3000
        if height > max_dimension or width > max_dimension:
            scale = max_dimension / max(height, width)
            new_height = int(height * scale)
            new_width = int(width * scale)
            return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        return image


# Global instance
image_preprocessor = ImagePreprocessor()
