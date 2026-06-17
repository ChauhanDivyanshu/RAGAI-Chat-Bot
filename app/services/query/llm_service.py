"""
LLM Service - Ollama Integration
Uses OpenAI-compatible API
"""
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from loguru import logger
from app.config import settings


class LLMService:
    """Service for calling Ollama LLM"""
    
    def __init__(self):
        # Ollama provides OpenAI-compatible API
        self.client = AsyncOpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama"  # Required but not used
        )
        self.main_model = settings.OLLAMA_MAIN_MODEL
        self.judge_model = settings.OLLAMA_JUDGE_MODEL
    
    async def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict],
        temperature: float = 0.3,
        max_tokens: int = 500
    ) -> Dict:
        """
        Generate answer using LLM with retrieved context
        
        Args:
            query: User question
            context_chunks: Retrieved chunks from vector search
            temperature: 0=deterministic, 1=creative
            max_tokens: Max response length
            
        Returns:
            {
                'answer': str,
                'sources': list,
                'model': str,
                'tokens_used': int
            }
        """
        if not context_chunks:
            return {
                'answer': "I don't have any relevant information to answer this question. Please upload relevant documents first.",
                'sources': [],
                'model': self.main_model,
                'tokens_used': 0
            }
        
        # Build context from chunks
        context_text = self._build_context(context_chunks)
        
        # Create prompt
        system_prompt = """You are a helpful AI assistant that answers questions based ONLY on the provided context.

Rules:
1. Answer ONLY using information from the context below
2. If the context doesn't contain enough information, say "I don't have enough information to answer this fully."
3. Be concise and accurate
4. Cite the source document name when possible
5. Do NOT make up information"""

        user_prompt = f"""Context from documents:
{context_text}

Question: {query}

Answer:"""

        try:
            logger.info(f"Calling Ollama model: {self.main_model}")
            
            response = await self.client.chat.completions.create(
                model=self.main_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            answer = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Build sources info
            sources = [
                {
                    'document_name': chunk['document_name'],
                    'page_number': chunk.get('page_number'),
                    'similarity_score': chunk['similarity_score'],
                    'preview': chunk['content'][:150] + '...' if len(chunk['content']) > 150 else chunk['content']
                }
                for chunk in context_chunks
            ]
            
            return {
                'answer': answer,
                'sources': sources,
                'model': self.main_model,
                'tokens_used': tokens_used
            }
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Format chunks into context string"""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            source = f"[Source {i}: {chunk['document_name']}"
            if chunk.get('page_number'):
                source += f", Page {chunk['page_number']}"
            source += f", Relevance: {chunk['similarity_score']:.2%}]"
            
            context_parts.append(f"{source}\n{chunk['content']}\n")
        
        return "\n---\n".join(context_parts)
    
    async def test_ollama(self) -> Dict:
        """Quick test to check Ollama is working"""
        try:
            response = await self.client.chat.completions.create(
                model=self.main_model,
                messages=[
                    {"role": "user", "content": "Say 'Hello, I am working!' in exactly 5 words."}
                ],
                max_tokens=50
            )
            return {
                'status': 'success',
                'model': self.main_model,
                'response': response.choices[0].message.content
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


# Global instance
llm_service = LLMService()
