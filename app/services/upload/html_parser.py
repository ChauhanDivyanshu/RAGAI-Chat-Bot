"""
HTML/TXT Parser - Web Pages and Plain Text
Handles HTML, HTM, TXT, MD files
"""
from pathlib import Path
from typing import Dict
import chardet
from bs4 import BeautifulSoup
import html2text

from app.utils import logger, ExtractionError, clean_text


class HTMLParser:
    """Parse HTML, plain text, and Markdown files"""
    
    def __init__(self):
        # Configure html2text for clean conversion
        self.h2t = html2text.HTML2Text()
        self.h2t.ignore_links = False
        self.h2t.ignore_images = True
        self.h2t.body_width = 0  # No line wrapping
    
    def extract(self, file_path: str, file_type: str = "html") -> Dict:
        """
        Extract text from HTML/TXT/MD file.
        
        Args:
            file_path: Path to file
            file_type: 'html', 'txt', 'md'
            
        Returns:
            {
                'full_text': str,
                'metadata': dict,
                'stats': dict
            }
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Parsing {file_type.upper()}: {path.name}")
        
        try:
            # Detect encoding
            with open(file_path, 'rb') as f:
                raw_data = f.read()
            
            detected = chardet.detect(raw_data)
            encoding = detected['encoding'] or 'utf-8'
            
            # Read content
            content = raw_data.decode(encoding, errors='replace')
            
            # Route to appropriate parser
            if file_type in ('html', 'htm'):
                return self._extract_html(content, encoding)
            else:  # txt, md
                return self._extract_text(content, encoding, file_type)
                
        except Exception as e:
            logger.error(f"{file_type.upper()} extraction failed: {e}")
            raise ExtractionError(file_type.upper(), str(e))
    
    def _extract_html(self, html_content: str, encoding: str) -> Dict:
        """Extract clean text from HTML"""
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract metadata
        metadata = self._extract_html_metadata(soup)
        
        # Remove scripts, styles, navigation
        for tag in soup(['script', 'style', 'noscript', 'iframe']):
            tag.decompose()
        
        # Get title
        title = soup.title.string if soup.title else ''
        
        # Convert to clean text (preserves structure)
        clean_html_text = self.h2t.handle(str(soup))
        
        # Final cleanup
        full_text = clean_text(clean_html_text)
        
        # Build result
        result = {
            'full_text': full_text,
            'metadata': {
                'title': title.strip() if title else '',
                'encoding': encoding,
                **metadata
            },
            'stats': {
                'total_characters': len(full_text),
                'word_count': len(full_text.split()),
                'has_title': bool(title)
            }
        }
        
        logger.info(
            f"HTML extracted: {result['stats']['word_count']} words "
            f"({encoding})"
        )
        
        return result
    
    def _extract_text(self, content: str, encoding: str, file_type: str) -> Dict:
        """Extract from plain text or markdown"""
        # Clean text
        full_text = clean_text(content) if file_type == 'txt' else content
        
        result = {
            'full_text': full_text,
            'metadata': {
                'encoding': encoding,
                'format': file_type
            },
            'stats': {
                'total_characters': len(full_text),
                'word_count': len(full_text.split()),
                'line_count': len(full_text.split('\n'))
            }
        }
        
        logger.info(
            f"{file_type.upper()} extracted: {result['stats']['word_count']} words "
            f"({encoding})"
        )
        
        return result
    
    def _extract_html_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from HTML head"""
        metadata = {}
        
        # Meta tags
        meta_tags = {
            'description': 'description',
            'keywords': 'keywords',
            'author': 'author',
            'viewport': 'viewport'
        }
        
        for key, name in meta_tags.items():
            tag = soup.find('meta', attrs={'name': name})
            if tag and tag.get('content'):
                metadata[key] = tag['content']
        
        # Open Graph tags
        og_tags = soup.find_all('meta', attrs={'property': lambda x: x and x.startswith('og:')})
        for tag in og_tags:
            prop = tag.get('property', '').replace('og:', 'og_')
            content = tag.get('content', '')
            if content:
                metadata[prop] = content
        
        return metadata


# Global instance
html_parser = HTMLParser()
