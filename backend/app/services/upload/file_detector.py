"""
File Type Detection Service
Smart multi-method detection with proper priority handling
"""
from pathlib import Path
from typing import Dict, Optional

try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

from app.utils import logger, get_file_extension, InvalidFileTypeError


class FileDetector:
    """Smart file type detection with priority logic"""
    
    SUPPORTED_TYPES = {
        # PDFs
        "pdf": {
            "extensions": ["pdf"],
            "mime_types": ["application/pdf"],
            "magic_bytes": [b"%PDF"],
            "category": "document",
            "max_size_mb": 50,
            "text_based": False
        },
        # Word documents
        "docx": {
            "extensions": ["docx"],
            "mime_types": [
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ],
            "magic_bytes": [b"PK\x03\x04"],
            "category": "document",
            "max_size_mb": 25,
            "text_based": False
        },
        "doc": {
            "extensions": ["doc"],
            "mime_types": ["application/msword"],
            "magic_bytes": [b"\xd0\xcf\x11\xe0"],
            "category": "document",
            "max_size_mb": 25,
            "text_based": False
        },
        # Excel
        "xlsx": {
            "extensions": ["xlsx"],
            "mime_types": [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ],
            "magic_bytes": [b"PK\x03\x04"],
            "category": "spreadsheet",
            "max_size_mb": 20,
            "text_based": False
        },
        "xls": {
            "extensions": ["xls"],
            "mime_types": ["application/vnd.ms-excel"],
            "magic_bytes": [b"\xd0\xcf\x11\xe0"],
            "category": "spreadsheet",
            "max_size_mb": 20,
            "text_based": False
        },
        # CSV (text-based)
        "csv": {
            "extensions": ["csv"],
            "mime_types": ["text/csv", "application/csv"],
            "magic_bytes": [],
            "category": "spreadsheet",
            "max_size_mb": 50,
            "text_based": True
        },
        # Plain text
        "txt": {
            "extensions": ["txt"],
            "mime_types": ["text/plain"],
            "magic_bytes": [],
            "category": "text",
            "max_size_mb": 10,
            "text_based": True
        },
        # HTML
        "html": {
            "extensions": ["html", "htm"],
            "mime_types": ["text/html"],
            "magic_bytes": [],
            "category": "text",
            "max_size_mb": 10,
            "text_based": True
        },
        # Markdown
        "md": {
            "extensions": ["md", "markdown"],
            "mime_types": ["text/markdown", "text/x-markdown"],
            "magic_bytes": [],
            "category": "text",
            "max_size_mb": 10,
            "text_based": True
        },
        # Images
        "jpg": {
            "extensions": ["jpg", "jpeg"],
            "mime_types": ["image/jpeg"],
            "magic_bytes": [b"\xff\xd8\xff"],
            "category": "image",
            "max_size_mb": 20,
            "text_based": False
        },
        "png": {
            "extensions": ["png"],
            "mime_types": ["image/png"],
            "magic_bytes": [b"\x89PNG\r\n\x1a\n"],
            "category": "image",
            "max_size_mb": 20,
            "text_based": False
        }
    }
    
    @classmethod
    def detect(
        cls,
        filename: str,
        content: bytes,
        provided_mime: Optional[str] = None
    ) -> Dict:
        """
        Detect file type using priority-based logic.
        
        Priority Order:
        1. Magic bytes (most reliable for binary files)
        2. Extension (most reliable for text files)
        3. libmagic detection
        4. MIME type from upload
        """
        ext = get_file_extension(filename)
        
        # Step 1: Try magic bytes first (for binary files)
        type_from_magic = cls._detect_by_magic_bytes(content)
        
        # Step 2: Extension-based detection
        type_from_ext = cls._detect_by_extension(ext)
        
        # Step 3: libmagic (if available)
        type_from_libmagic = None
        if MAGIC_AVAILABLE:
            try:
                detected_mime = magic.from_buffer(content[:2048], mime=True)
                type_from_libmagic = cls._detect_by_mime(detected_mime)
            except Exception as e:
                logger.debug(f"libmagic detection failed: {e}")
        
        # Step 4: Provided MIME type
        type_from_mime = cls._detect_by_mime(provided_mime) if provided_mime else None
        
        # ─── PRIORITY DECISION LOGIC ───
        detected_type = None
        confidence = "low"
        methods_used = []
        
        # Rule 1: If magic bytes detected, use it (most reliable for binary)
        if type_from_magic:
            detected_type = type_from_magic
            confidence = "high"
            methods_used.append("magic_bytes")
            
            # Cross-check with extension
            if type_from_ext == type_from_magic:
                methods_used.append("extension")
                confidence = "very_high"
        
        # Rule 2: For text-based files (no magic bytes), TRUST extension
        elif type_from_ext and cls.SUPPORTED_TYPES.get(type_from_ext, {}).get("text_based"):
            detected_type = type_from_ext
            confidence = "high"  # Extension is reliable for text files
            methods_used.append("extension")
            
            # Bonus confidence if MIME matches
            if type_from_mime == type_from_ext:
                methods_used.append("mime_type")
                confidence = "very_high"
            
            # Verify content looks like text (not binary)
            if cls._is_text_content(content):
                methods_used.append("content_analysis")
        
        # Rule 3: Extension-based for other files
        elif type_from_ext:
            detected_type = type_from_ext
            confidence = "medium"
            methods_used.append("extension")
        
        # Rule 4: libmagic fallback
        elif type_from_libmagic:
            detected_type = type_from_libmagic
            confidence = "medium"
            methods_used.append("libmagic")
        
        # Rule 5: MIME type fallback (least reliable)
        elif type_from_mime:
            detected_type = type_from_mime
            confidence = "low"
            methods_used.append("mime_type")
        
        # ─── VALIDATION ───
        if not detected_type:
            raise InvalidFileTypeError(
                ext or "unknown",
                list(cls.SUPPORTED_TYPES.keys())
            )
        
        # Get config
        config = cls.SUPPORTED_TYPES[detected_type]
        
        result = {
            "file_type": detected_type,
            "mime_type": config["mime_types"][0],
            "category": config["category"],
            "max_size_mb": config["max_size_mb"],
            "max_size_bytes": config["max_size_mb"] * 1024 * 1024,
            "detection_method": "+".join(methods_used),
            "confidence": confidence,
            "extension": ext,
            "text_based": config.get("text_based", False)
        }
        
        logger.info(
            f"Detected: {filename} -> {detected_type} "
            f"({config['category']}, {confidence} confidence, "
            f"via {result['detection_method']})"
        )
        
        return result
    
    @classmethod
    def _detect_by_extension(cls, extension: str) -> Optional[str]:
        """Detect type from file extension"""
        if not extension:
            return None
        
        ext = extension.lower().lstrip('.')
        
        for file_type, config in cls.SUPPORTED_TYPES.items():
            if ext in config["extensions"]:
                return file_type
        return None
    
    @classmethod
    def _detect_by_magic_bytes(cls, content: bytes) -> Optional[str]:
        """Detect type from magic bytes (file signature)"""
        if not content or len(content) < 4:
            return None
        
        header = content[:16]
        
        for file_type, config in cls.SUPPORTED_TYPES.items():
            for magic_bytes in config["magic_bytes"]:
                if header.startswith(magic_bytes):
                    if magic_bytes == b"PK\x03\x04":
                        return cls._detect_zip_based(content)
                    return file_type
        return None
    
    @classmethod
    def _detect_zip_based(cls, content: bytes) -> Optional[str]:
        """Differentiate ZIP-based formats (DOCX vs XLSX)"""
        sample = content[:4096]
        
        if b"word/" in sample:
            return "docx"
        elif b"xl/" in sample:
            return "xlsx"
        elif b"ppt/" in sample:
            return None
        return None
    
    @classmethod
    def _detect_by_mime(cls, mime_type: Optional[str]) -> Optional[str]:
        """Detect type from MIME string"""
        if not mime_type:
            return None
        
        mime_type = mime_type.lower().split(';')[0].strip()
        
        for file_type, config in cls.SUPPORTED_TYPES.items():
            if mime_type in config["mime_types"]:
                return file_type
        return None
    
    @classmethod
    def _is_text_content(cls, content: bytes, sample_size: int = 1024) -> bool:
        """Check if content appears to be text (not binary)"""
        if not content:
            return False
        
        sample = content[:sample_size]
        
        # Try to decode as UTF-8
        try:
            sample.decode('utf-8')
            return True
        except UnicodeDecodeError:
            pass
        
        # Try other common encodings
        for encoding in ['latin-1', 'cp1252', 'utf-16']:
            try:
                sample.decode(encoding)
                return True
            except UnicodeDecodeError:
                continue
        
        return False
    
    @classmethod
    def get_supported_types(cls) -> Dict[str, list]:
        """Get list of all supported file types grouped by category"""
        result = {}
        for file_type, config in cls.SUPPORTED_TYPES.items():
            category = config["category"]
            if category not in result:
                result[category] = []
            result[category].append({
                "type": file_type,
                "extensions": config["extensions"],
                "max_size_mb": config["max_size_mb"]
            })
        return result
    
    @classmethod
    def is_supported(cls, file_type: str) -> bool:
        """Check if file type is supported"""
        return file_type.lower() in cls.SUPPORTED_TYPES


# Global instance
file_detector = FileDetector()
