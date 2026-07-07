import pytesseract
from PIL import Image
import numpy as np
from typing import List, Optional
import logging
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRService:
    """Handles OCR for Hindi and English text extraction"""
    
    def __init__(self):
        self._reader = None
    
    @property
    def reader(self):
        """Lazy loader for EasyOCR reader"""
        if self._reader is None:
            self.initialize_ocr()
        return self._reader
    
    def initialize_ocr(self):
        """Initialize EasyOCR for Hindi/English"""
        try:
            import easyocr
            self._reader = easyocr.Reader(
                settings.OCR_LANGUAGES,  # Now this exists in config
                gpu=settings.OCR_GPU,
                verbose=False
            )
            logger.info("✅ EasyOCR initialized for Hindi/English")
        except Exception as e:
            logger.error(f"Failed to initialize EasyOCR: {e}")
            self._reader = None
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using EasyOCR"""
        if self.reader is None:
            return ""
        try:
            result = self.reader.readtext(image_path, detail=0)
            return ' '.join(result)
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            return ""
    
    def extract_text_from_image_pil(self, image: Image.Image) -> str:
        """Extract text from PIL Image object"""
        if self.reader is None:
            return ""
        try:
            img_array = np.array(image)
            result = self.reader.readtext(img_array, detail=0)
            return ' '.join(result)
        except Exception as e:
            logger.error(f"OCR failed for PIL image: {e}")
            return ""
    
    def extract_text_from_pdf_page(self, page_image: Image.Image) -> str:
        """Extract text from a PDF page image"""
        if self.reader is None:
            return ""
        try:
            result = self.reader.readtext(np.array(page_image), detail=0)
            text = ' '.join(result)
            return text
        except Exception as e:
            logger.error(f"Page OCR failed: {e}")
            return ""

# Global instance
ocr_service = OCRService()