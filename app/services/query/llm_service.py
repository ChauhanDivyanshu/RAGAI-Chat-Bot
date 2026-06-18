"""
LLM Service - SUPER SMART Handler
Handles 20+ intents with natural responses
"""
from typing import List, Dict, Optional, AsyncGenerator
from openai import AsyncOpenAI
import asyncio
import re
from app.config import settings
from app.utils import logger, LLMServiceError


class LLMService:
    """Super smart LLM service"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",
            timeout=120.0
        )
        self.main_model = settings.OLLAMA_MAIN_MODEL
        self.judge_model = settings.OLLAMA_JUDGE_MODEL
    
    def detect_language(self, text: str) -> str:
        """Detect query language"""
        if not text:
            return "english"
        
        hindi_chars = len(re.findall(r'[\u0900-\u097F]', text))
        total_chars = len(re.sub(r'\s', '', text))
        
        if total_chars == 0:
            return "english"
        
        hindi_ratio = hindi_chars / total_chars
        
        if hindi_ratio > 0.3:
            return "hindi"
        
        hinglish_keywords = [
            'kya', 'kaun', 'kahan', 'kab', 'kaise', 'kyun', 'kyu',
            'hai', 'hain', 'tha', 'thi', 'ho', 'hoga',
            'mera', 'meri', 'tera', 'teri', 'aap', 'tum',
            'batao', 'bata', 'chahiye', 'karna', 'karo',
            'mujhe', 'tujhe', 'acha', 'accha', 'theek',
            'nahi', 'nahin', 'haan', 'han', 'bhai', 'yaar',
        ]
        
        text_lower = text.lower()
        count = sum(1 for word in hinglish_keywords if re.search(r'\b' + word + r'\b', text_lower))
        
        if count >= 2:
            return "hinglish"
        if count >= 1 and len(text.split()) < 8:
            return "hinglish"
        
        return "english"
    
    async def generate_smart_response(
        self,
        query: str,
        context_chunks: Optional[List[Dict]] = None,
        intent: Optional[Dict] = None
    ) -> Dict:
        """Smart response generation based on intent"""
        from app.services.query.intent_classifier import intent_classifier
        from app.services.query.response_templates import templates
        
        if not intent:
            intent = intent_classifier.classify(query)
        
        intent_type = intent['intent']
        language = intent['language_hint']
        use_rag = intent['use_rag']
        response_type = intent.get('response_type', 'direct')
        
        logger.info(f"Intent: {intent_type}, Language: {language}, Type: {response_type}")
        
        # ─── DIRECT TEMPLATE RESPONSES (Instant!) ───
        template_intents = [
            'greeting', 'morning_greeting', 'afternoon_greeting',
            'evening_greeting', 'night_greeting', 'how_are_you',
            'farewell', 'thanks', 'compliment', 'complaint',
            'sad_emotion', 'happy_emotion', 'tired_emotion', 'bored_emotion',
            'what_doing', 'busy_question', 'approval', 'rejection',
            'confusion', 'time_question', 'date_question',
            'help', 'identity'
        ]
        
        if intent_type in template_intents:
            answer = templates.get_response(intent_type, language)
            return self._make_response(answer, language, intent_type)
        
        # ─── LLM DIRECT (No RAG) ───
        if intent_type in ['translation', 'math', 'joke_request', 'general_chat']:
            return await self._generate_direct_llm(query, language, intent_type)
        
        # ─── RAG QUERY ───
        if intent_type == 'document_query':
            if not context_chunks:
                return self._make_response(
                    templates.get_no_documents(language), language, intent_type
                )
            return await self._generate_rag_response(query, context_chunks, language)
        
        return await self._generate_direct_llm(query, language, 'general_chat')
    
    def _make_response(self, answer: str, language: str, intent: str) -> Dict:
        """Build response dict"""
        return {
            'answer': answer,
            'sources': [],
            'model': 'template',
            'tokens_used': 0,
            'language': language,
            'intent': intent
        }
    
    async def _generate_direct_llm(
        self,
        query: str,
        language: str,
        intent_type: str
    ) -> Dict:
        """Generate response using LLM WITHOUT document context"""
        
        if intent_type == 'translation':
            system_prompt = self._get_translation_prompt(language)
        elif intent_type == 'math':
            system_prompt = self._get_math_prompt(language)
        elif intent_type == 'joke_request':
            system_prompt = self._get_joke_prompt(language)
        else:
            system_prompt = self._get_general_prompt(language)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.main_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.5 if intent_type == 'joke_request' else 0.2,
                max_tokens=200,
                stop=["\n\nUser:", "\n\nQuestion:"]
            )
            
            answer = response.choices[0].message.content.strip()
            answer = self._clean_response(answer)
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return {
                'answer': answer,
                'sources': [],
                'model': self.main_model,
                'tokens_used': tokens_used,
                'language': language,
                'intent': intent_type
            }
        except Exception as e:
            logger.error(f"Direct LLM call failed: {e}")
            raise LLMServiceError(f"LLM error: {str(e)}")
    
    async def _generate_rag_response(
        self,
        query: str,
        context_chunks: List[Dict],
        language: str
    ) -> Dict:
        """RAG response generation"""
        top_chunks = context_chunks[:3]
        has_table = self._has_tabular_content(top_chunks)
        context_text = self._build_clean_context(top_chunks)
        
        system_prompt = self._get_rag_prompt(language, has_table)
        user_prompt = self._get_rag_user_prompt(language, context_text, query)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.main_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=350,
                stop=["\n\nQUESTION:", "\n\n=== DOCUMENT"]
            )
            
            answer = response.choices[0].message.content.strip()
            answer = self._clean_response(answer)
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            sources = [
                {
                    'document_name': chunk['document_name'],
                    'page_number': chunk.get('page_number'),
                    'similarity_score': chunk['similarity_score'],
                    'preview': chunk['content'][:200] + '...' if len(chunk['content']) > 200 else chunk['content']
                }
                for chunk in top_chunks
            ]
            
            return {
                'answer': answer,
                'sources': sources,
                'model': self.main_model,
                'tokens_used': tokens_used,
                'language': language,
                'intent': 'document_query'
            }
        except Exception as e:
            logger.error(f"RAG LLM call failed: {e}")
            raise LLMServiceError(f"LLM error: {str(e)}")
    
    def _clean_response(self, text: str) -> str:
        """Clean response"""
        fluff_phrases = [
            "Namoona!", "Main aapki sawaal ka jawab dena chahta hoon.",
            "Let me help you with that.", "I'd be happy to help.",
            "Based on the provided context,", "According to the document,",
            "From the information given,", "Looking at the document content,",
        ]
        
        cleaned = text
        for phrase in fluff_phrases:
            cleaned = cleaned.replace(phrase, "").strip()
        
        # Remove duplicates
        lines = cleaned.split('\n')
        seen = set()
        unique_lines = []
        for line in lines:
            line_clean = line.strip().lower()
            if line_clean and line_clean not in seen:
                seen.add(line_clean)
                unique_lines.append(line)
            elif not line_clean:
                unique_lines.append(line)
        
        cleaned = '\n'.join(unique_lines)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()
    
    def _get_translation_prompt(self, language: str) -> str:
        return """You are a translator. Translate the given text accurately.

Rules:
1. ONLY provide the translation
2. Show original and translated text
3. Add pronunciation if helpful
4. Be brief

Example:
User: "Translate to Hindi: Hello"
Response: "Hello → नमस्ते (Namaste)"
"""
    
    def _get_math_prompt(self, language: str) -> str:
        return """You are a math assistant. Solve and provide ONLY the answer.

Rules:
1. Show calculation briefly
2. Give final answer clearly
3. No long explanations"""
    
    def _get_joke_prompt(self, language: str) -> str:
        if language == 'hindi':
            return "आप एक मज़ेदार AI हैं। एक छोटा सा funny joke हिंदी में सुनाएं।"
        elif language == 'hinglish':
            return "Tum ek funny AI ho. Ek chota sa mazedaar joke Hinglish mein sunao."
        else:
            return "You are a funny AI. Tell a short, family-friendly joke."
    
    def _get_general_prompt(self, language: str) -> str:
        if language == 'hindi':
            return "आप एक मित्रवत AI हैं। Short और helpful जवाब हिंदी में दें।"
        elif language == 'hinglish':
            return "Tum ek friendly AI ho. Short aur helpful answer Hinglish mein do."
        else:
            return "You are a friendly AI. Give short, helpful answers."
    
    def _get_rag_prompt(self, language: str, has_table: bool) -> str:
        if language == 'hindi':
            base = """आप एक precise AI हैं। केवल document content से जवाब दें।

नियम:
1. ✅ Direct और clear जवाब
2. ✅ Specific information quote करें
3. ✅ Confidently बताएं अगर answer मिल जाए
4. ❌ Fluff मत add करें
5. ❌ Same baat बार-बार मत कहें"""
        elif language == 'hinglish':
            base = """Tum precise AI ho. Sirf document content se jawab do.

Rules:
1. ✅ Direct aur clear answer
2. ✅ Specific information quote karo
3. ✅ Confidently batao agar answer mil jaye
4. ❌ Fluff mat add karo
5. ❌ Same baat baar-baar mat kaho"""
        else:
            base = """You are a precise AI. Answer ONLY from document content.

Rules:
1. ✅ Direct and clear answer
2. ✅ Quote specific information
3. ✅ Be confident when answer is in document
4. ❌ No fluff
5. ❌ Don't repeat"""
        
        if has_table:
            base += "\n\nNote: Content has tabular data. Read carefully."
        
        return base
    
    def _get_rag_user_prompt(self, language: str, context: str, query: str) -> str:
        if language == 'hindi':
            return f"""DOCUMENT CONTENT:
{context}

QUESTION: {query}

ANSWER (हिंदी में, direct):"""
        elif language == 'hinglish':
            return f"""DOCUMENT CONTENT:
{context}

QUESTION: {query}

ANSWER (Hinglish, direct):"""
        else:
            return f"""DOCUMENT CONTENT:
{context}

QUESTION: {query}

ANSWER (direct):"""
    
    def _has_tabular_content(self, chunks: List[Dict]) -> bool:
        for chunk in chunks:
            content = chunk.get('content', '')
            lines = content.split('\n')
            pipe_lines = sum(1 for line in lines if '|' in line)
            if len(lines) > 2 and pipe_lines / len(lines) > 0.3:
                return True
        return False
    
    def _build_clean_context(self, chunks: List[Dict]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            content = chunk['content'].strip()
            if content:
                if len(content) > 1500:
                    content = content[:1500] + "..."
                doc_name = chunk.get('document_name', 'Document')
                page = chunk.get('page_number')
                source_label = f"[Source {i}: {doc_name}"
                if page:
                    source_label += f", Page {page}"
                source_label += "]"
                parts.append(f"{source_label}\n{content}")
        return "\n\n---\n\n".join(parts)
    
    async def generate_answer(self, query, context_chunks, temperature=0.1, max_tokens=500):
        """Legacy method"""
        from app.services.query.intent_classifier import intent_classifier
        intent = intent_classifier.classify(query)
        return await self.generate_smart_response(query, context_chunks, intent)
    
    def _get_no_context_message(self, query: str) -> str:
        from app.services.query.response_templates import templates
        language = self.detect_language(query)
        return templates.get_no_documents(language)
    
    async def generate_answer_streaming(self, query, context_chunks, temperature=0.1, max_tokens=500):
        result = await self.generate_smart_response(query, context_chunks)
        for char in result['answer']:
            yield char
            await asyncio.sleep(0.01)
    
    async def test_ollama(self):
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
        except Exception as e:
            return {'status': 'error', 'model': self.main_model, 'error': str(e)}


llm_service = LLMService()
