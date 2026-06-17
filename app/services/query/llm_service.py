"""
LLM Service - Ollama Integration (OPTIMIZED)
Production-grade with streaming, caching, and smart context management
"""
from typing import List, Dict, Optional, AsyncGenerator
from openai import AsyncOpenAI
import asyncio
from app.config import settings
from app.utils import logger, LLMServiceError


class LLMService:
    """Optimized LLM service for fast inference"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",
            timeout=120.0  # 2 minute timeout
        )
        self.main_model = settings.OLLAMA_MAIN_MODEL
        self.judge_model = settings.OLLAMA_JUDGE_MODEL
    
    async def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict],
        temperature: float = 0.1,  # Lower for speed + accuracy
        max_tokens: int = 300       # Shorter responses
    ) -> Dict:
        """
        Generate concise answer with optimized prompting
        """
        if not context_chunks:
            return {
                'answer': "I don't have relevant information to answer this question. Please upload relevant documents.",
                'sources': [],
                'model': self.main_model,
                'tokens_used': 0
            }
        
        # OPTIMIZATION: Use only top 3 chunks (less context = faster)
        top_chunks = context_chunks[:3]
        
        # OPTIMIZATION: Compact context format
        context_text = self._build_compact_context(top_chunks)
        
        # OPTIMIZATION: Concise prompts (shorter = faster)
        system_prompt = "You are a precise assistant. Answer based ONLY on the context. Be concise. If unsure, say so."
        
        user_prompt = f"""Context:
{context_text}

Question: {query}

Concise answer:"""
        
        try:
            logger.info(f"Calling {self.main_model} (context: {len(context_text)} chars)")
            
            response = await self.client.chat.completions.create(
                model=self.main_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                # OPTIMIZATION: Stop tokens to prevent rambling
                stop=["\n\nQuestion:", "\n\nContext:", "\n\nSource:"]
            )
            
            answer = response.choices[0].message.content.strip()
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            # Build sources
            sources = [
                {
                    'document_name': chunk['document_name'],
                    'page_number': chunk.get('page_number'),
                    'similarity_score': chunk['similarity_score'],
                    'preview': chunk['content'][:150] + '...' if len(chunk['content']) > 150 else chunk['content']
                }
                for chunk in top_chunks
            ]
            
            return {
                'answer': answer,
                'sources': sources,
                'model': self.main_model,
                'tokens_used': tokens_used
            }
            
        except asyncio.TimeoutError:
            logger.error("LLM call timed out")
            raise LLMServiceError("LLM response timed out. Try a shorter question.")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise LLMServiceError(f"LLM error: {str(e)}")
    
    def _build_compact_context(self, chunks: List[Dict]) -> str:
        """Build minimal context (token-optimized)"""
        # OPTIMIZATION: No verbose source markers, just content
        parts = []
        for i, chunk in enumerate(chunks, 1):
            # Truncate very long chunks
            content = chunk['content']
            if len(content) > 800:
                content = content[:800] + "..."
            parts.append(f"[{i}] {content}")
        
        return "\n\n".join(parts)
    
    async def generate_answer_streaming(
        self,
        query: str,
        context_chunks: List[Dict],
        temperature: float = 0.1,
        max_tokens: int = 300
    ) -> AsyncGenerator[str, None]:
        """
        STREAMING version - yields tokens as they're generated
        Much better UX - user sees answer building up
        """
        if not context_chunks:
            yield "No relevant information found."
            return
        
        top_chunks = context_chunks[:3]
        context_text = self._build_compact_context(top_chunks)
        
        system_prompt = "You are a precise assistant. Answer based ONLY on the context. Be concise."
        user_prompt = f"Context:\n{context_text}\n\nQuestion: {query}\n\nAnswer:"
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.main_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True  # ENABLE STREAMING
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"Error: {str(e)}"
    
    async def test_ollama(self) -> Dict:
        """Quick connectivity test"""
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.main_model,
                    messages=[{"role": "user", "content": "Reply with just 'OK'"}],
                    max_tokens=10,
                    temperature=0
                ),
                timeout=30.0
            )
            return {
                'status': 'success',
                'model': self.main_model,
                'response': response.choices[0].message.content.strip()
            }
        except asyncio.TimeoutError:
            return {
                'status': 'error',
                'model': self.main_model,
                'error': 'Timeout - Ollama too slow'
            }
        except Exception as e:
            return {
                'status': 'error',
                'model': self.main_model,
                'error': str(e)
            }


# Global instance
llm_service = LLMService()
