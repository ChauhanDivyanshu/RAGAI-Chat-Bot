"""
Text Chunking Service
Splits text into manageable chunks for embeddings
"""
from typing import List, Dict
import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger
from app.config import settings


class TextChunker:
    """Smart text chunking with token awareness"""
    
    def __init__(self):
        # Use tiktoken for accurate token counting (GPT tokenizer)
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Create splitter
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE * 4,  # ~512 tokens = ~2048 chars
            chunk_overlap=settings.CHUNK_OVERLAP * 4,  # ~50 tokens = ~200 chars
            length_function=self.count_tokens,
            separators=[
                "\n\n",      # Paragraphs
                "\n",        # Lines
                ". ",        # Sentences
                "? ",
                "! ",
                "; ",
                ", ",
                " ",         # Words
                ""           # Characters (last resort)
            ]
        )
    
    def count_tokens(self, text: str) -> int:
        """Count tokens accurately"""
        return len(self.tokenizer.encode(text))
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into chunks
        
        Args:
            text: Input text to chunk
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunks with metadata:
            [{
                'content': str,
                'chunk_index': int,
                'token_count': int,
                'char_count': int,
                'metadata': dict
            }]
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for chunking")
            return []
        
        logger.info(f"Chunking text of {len(text)} characters...")
        
        # Split into chunks
        text_chunks = self.splitter.split_text(text)
        
        # Create chunk objects with metadata
        chunks = []
        for idx, chunk_text in enumerate(text_chunks):
            chunks.append({
                'content': chunk_text.strip(),
                'chunk_index': idx,
                'token_count': self.count_tokens(chunk_text),
                'char_count': len(chunk_text),
                'metadata': metadata or {}
            })
        
        logger.info(
            f"Created {len(chunks)} chunks "
            f"(avg {sum(c['token_count'] for c in chunks) // len(chunks) if chunks else 0} tokens each)"
        )
        
        return chunks
    
    def chunk_pages(self, pages: List[Dict]) -> List[Dict]:
        """
        Chunk page-by-page (preserves page numbers)
        
        Args:
            pages: List of {'page_number': int, 'text': str}
            
        Returns:
            List of chunks with page_number in metadata
        """
        all_chunks = []
        global_index = 0
        
        for page in pages:
            page_chunks = self.chunk_text(
                page['text'],
                metadata={'page_number': page['page_number']}
            )
            
            # Renumber globally
            for chunk in page_chunks:
                chunk['chunk_index'] = global_index
                chunk['page_number'] = page['page_number']
                global_index += 1
            
            all_chunks.extend(page_chunks)
        
        return all_chunks


# Global instance
chunker = TextChunker()
