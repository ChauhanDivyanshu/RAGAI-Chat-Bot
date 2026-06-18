"""
LLM Service - PRODUCTION READY with GROQ
Ultra-fast responses with Groq + Ollama fallback
"""
from typing import List, Dict, Optional, AsyncGenerator
import asyncio
import re
from app.config import settings
from app.utils import logger, LLMServiceError


class LLMService:
    """Production-grade LLM service with Groq priority"""
    
    def __init__(self):
        self.use_groq = settings.USE_GROQ and bool(settings.GROQ_API_KEY)
        
        if self.use_groq:
            try:
                from groq import AsyncGroq
                self.client = AsyncGroq(
                    api_key=settings.GROQ_API_KEY,
                    timeout=30.0
                )
                self.main_model = settings.GROQ_MODEL
                self.judge_model = settings.GROQ_MODEL
                logger.info(f" LLM Service: GROQ ({self.main_model}) - PRODUCTION MODE")
            except ImportError:
                logger.error(" Groq not installed. Run: pip install groq")
                self._init_ollama()
            except Exception as e:
                logger.error(f" Groq failed: {e}, using Ollama")
                self._init_ollama()
        else:
            self._init_ollama()
    
    def _init_ollama(self):
        """Fallback to Ollama"""
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",
            timeout=120.0
        )
        self.main_model = settings.OLLAMA_MAIN_MODEL
        self.judge_model = settings.OLLAMA_JUDGE_MODEL
        self.use_groq = False
        logger.info(f" LLM Service: OLLAMA ({self.main_model}) - LOCAL MODE")
    
    
    # ═══════════════════════════════════════════════
    # 🌐 LANGUAGE DETECTION
    # ═══════════════════════════════════════════════
    
    def detect_language(self, text: str) -> str:
        """Detect query language with high accuracy"""
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
            'kitne', 'sakta', 'sakte',
        ]
        
        text_lower = text.lower()
        count = sum(1 for word in hinglish_keywords if re.search(r'\b' + word + r'\b', text_lower))
        
        if count >= 2:
            return "hinglish"
        if count >= 1 and len(text.split()) < 8:
            return "hinglish"
        
        return "english"
    
    # ═══════════════════════════════════════════════
    # 🎯 MAIN RESPONSE GENERATOR
    # ═══════════════════════════════════════════════
    
    async def generate_smart_response(
        self,
        query: str,
        context_chunks: Optional[List[Dict]] = None,
        intent: Optional[Dict] = None
    ) -> Dict:
        """Smart response with multi-intent handling"""
        from app.services.query.intent_classifier import intent_classifier
        from app.services.query.response_templates import templates
        
        if not intent:
            intent = intent_classifier.classify(query)
        
        intent_type = intent['intent']
        language = intent['language_hint']
        use_rag = intent['use_rag']
        
        logger.info(f" Intent: {intent_type} | Lang: {language} | RAG: {use_rag}")
        
        # ─── INSTANT TEMPLATE RESPONSES ───
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
        return {
            'answer': answer,
            'sources': [],
            'model': 'template',
            'tokens_used': 0,
            'language': language,
            'intent': intent
        }
    
    # ═══════════════════════════════════════════════
    # 🤖 DIRECT LLM (No Documents)
    # ═══════════════════════════════════════════════
    
    async def _generate_direct_llm(
        self,
        query: str,
        language: str,
        intent_type: str
    ) -> Dict:
        """Generate without document context"""
        
        if intent_type == 'translation':
            system_prompt = self._get_translation_prompt(language)
            temperature = 0.2
            max_tokens = 250
        elif intent_type == 'math':
            system_prompt = self._get_math_prompt(language)
            temperature = 0.1
            max_tokens = 200
        elif intent_type == 'joke_request':
            system_prompt = self._get_joke_prompt(language)
            temperature = 0.8
            max_tokens = 200
        else:
            system_prompt = self._get_general_prompt(language)
            temperature = 0.5
            max_tokens = 300
        
        try:
            response = await self.client.chat.completions.create(
                model=self.main_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
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
            logger.error(f" Direct LLM failed: {e}")
            raise LLMServiceError(f"LLM error: {str(e)}")
    
    # ═══════════════════════════════════════════════
    # 📚 RAG RESPONSE (Document-based) - THE BIG FIX!
    # ═══════════════════════════════════════════════
    
    async def _generate_rag_response(
        self,
        query: str,
        context_chunks: List[Dict],
        language: str
    ) -> Dict:
        """FAST RAG response generation"""
        
        # ⚡ SPEED: Only top 2 chunks
        top_chunks = context_chunks[:2]  # Was 5, now 2
        has_table = self._has_tabular_content(top_chunks)
        context_text = self._build_clean_context(top_chunks)
        
        system_prompt = self._get_rag_prompt(language, has_table)
        user_prompt = self._get_rag_user_prompt(language, context_text, query)
        
        logger.info(f" Context: {len(context_text)} chars, {len(top_chunks)} chunks")
        
        try:
            response = await self.client.chat.completions.create(
                model=self.main_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=400,  # ⚡ Reduced from 800 to 400
                top_p=0.9,
            )
            
            answer = response.choices[0].message.content.strip()
            answer = self._clean_response(answer)
            
            if self._is_low_quality(answer):
                answer = self._fallback_answer(language)
            
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
            logger.error(f" RAG LLM failed: {e}")
            raise LLMServiceError(f"LLM error: {str(e)}")
    
    # ═══════════════════════════════════════════════
    # 🧹 RESPONSE QUALITY CHECKS
    # ═══════════════════════════════════════════════
    
    def _is_low_quality(self, answer: str) -> bool:
        """Detect bad LLM responses"""
        if not answer or len(answer.strip()) < 10:
            return True
        
        bad_indicators = [
            "i don't know",
            "i cannot",
            "as an ai",
            "i'm just an ai",
            "i don't have access",
            "i'm not able to",
        ]
        
        answer_lower = answer.lower()
        bad_count = sum(1 for ind in bad_indicators if ind in answer_lower)
        
        # If answer is short AND has bad indicators
        if len(answer) < 50 and bad_count > 0:
            return True
        
        return False
    
    def _fallback_answer(self, language: str) -> str:
        """Fallback when answer is bad"""
        if language == 'hindi':
            return "मुझे आपके documents में इस सवाल का सटीक जवाब नहीं मिल पाया। कृपया अपना सवाल अलग तरीके से पूछें।"
        elif language == 'hinglish':
            return "Mujhe aapke documents mein is sawal ka exact jawab nahi mil paya. Please apna question alag tareeke se puchein."
        else:
            return "I couldn't find a precise answer to your question in the documents. Please try rephrasing your question."
    
    def _clean_response(self, text: str) -> str:
        """Clean response text"""
        fluff_phrases = [
            "Based on the provided context,",
            "Based on the context provided,",
            "According to the document,",
            "According to the documents,",
            "From the information given,",
            "Looking at the document content,",
            "Based on the documents,",
            "From the context,",
        ]
        
        cleaned = text
        for phrase in fluff_phrases:
            cleaned = cleaned.replace(phrase, "").strip()
            cleaned = cleaned.replace(phrase.lower(), "").strip()
        
        # Remove duplicate consecutive lines
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
        cleaned = re.sub(r' {2,}', ' ', cleaned)
        
        return cleaned.strip()
    
    # ═══════════════════════════════════════════════
    # 🎨 PROMPT TEMPLATES (THE SECRET SAUCE!)
    # ═══════════════════════════════════════════════
    
    def _get_translation_prompt(self, language: str) -> str:
        return """You are an expert translator. Translate accurately.

RULES:
1. Provide translation directly
2. Show: Original → Translation (Pronunciation if helpful)
3. Be concise, no extra explanation

EXAMPLES:
"Translate to Hindi: Hello" → "Hello → नमस्ते (Namaste)"
"Translate to English: धन्यवाद" → "धन्यवाद → Thank you"
"""
    
    def _get_math_prompt(self, language: str) -> str:
        return """You are a math assistant. Solve precisely.

RULES:
1. Show brief calculation
2. Give final answer clearly
3. No long explanations

FORMAT:
Calculation: [steps]
Answer: [result]
"""
    
    def _get_joke_prompt(self, language: str) -> str:
        if language == 'hindi':
            return """आप एक मज़ेदार AI हैं। एक छोटा, साफ-सुथरा हिंदी joke सुनाएं।
केवल joke बताएं, कोई introduction नहीं।"""
        elif language == 'hinglish':
            return """Tum funny AI ho. Ek chota, clean Hinglish joke sunao.
Sirf joke batao, koi intro nahi."""
        else:
            return """You are a funny AI. Tell ONE short, clean, family-friendly joke.
Just the joke, no introduction."""
    
    def _get_general_prompt(self, language: str) -> str:
        if language == 'hindi':
            return """आप एक मित्रवत AI assistant हैं। Short, helpful और natural जवाब दें।
2-3 lines में जवाब दें, अनावश्यक details नहीं।"""
        elif language == 'hinglish':
            return """Tum friendly AI assistant ho. Short, helpful aur natural answer do.
2-3 lines mein answer do, unnecessary details nahi."""
        else:
            return """You are a friendly AI assistant. Give short, helpful, natural answers.
Answer in 2-3 lines, no unnecessary details."""
    
    # ═══════════════════════════════════════════════
    # 🎯 RAG PROMPT (THE MAIN MAGIC!)
    # ═══════════════════════════════════════════════
    
    def _get_rag_prompt(self, language: str, has_table: bool) -> str:
        """Production-grade RAG prompt"""
        
        if language == 'hindi':
            base = """आप एक expert AI assistant हैं जो documents से सटीक जवाब देते हैं।

# मुख्य नियम (बहुत ज़रूरी!)

## नियम 1: केवल Document Content से जवाब
- ✅ ONLY दिए गए document content से जवाब दें
- ❌ अपनी जानकारी से कुछ मत जोड़ें
- ❌ कुछ भी guess मत करें या बनाएं

## नियम 2: सटीक और Direct जवाब
- ✅ Specific numbers, dates, names quote करें
- ✅ Direct point पर आएं
- ✅ Confidence के साथ बताएं अगर info मिले
- ❌ "Based on context" जैसी fluff मत use करें

## नियम 3: अगर जवाब नहीं मिले
- साफ-साफ बताएं: "मुझे documents में इस बारे में जानकारी नहीं मिली"
- कोई बहाना मत बनाएं

## नियम 4: Response Format
- Short questions → 2-3 lines में जवाब
- Detailed questions → bullet points use करें
- Numbers/data → **bold** करें important parts
- Multiple sources → combine करें intelligently

## नियम 5: Source Citation
- अगर specific source से info ली → mention करें: "[Document Name, Page X के अनुसार]"

# उदाहरण
Question: "Leave policy क्या है?"
Bad: "Leave के बारे में documents में कुछ है..."
Good: "Company की leave policy के अनुसार:
- **Sick Leave:** 12 दिन/साल
- **Casual Leave:** 8 दिन/साल
- **Earned Leave:** 15 दिन/साल

[Source: HR Policy Document, Page 3]"
"""
        elif language == 'hinglish':
            base = """Tum expert AI assistant ho jo documents se accurate jawab dete ho.

# Main Rules (BAHUT IMPORTANT!)

## Rule 1: Sirf Document Content Se Jawab
- ✅ ONLY diye gaye document content se jawab do
- ❌ Apni knowledge se kuch add mat karo
- ❌ Kuch bhi guess ya make-up mat karo

## Rule 2: Accurate Aur Direct Jawab
- ✅ Specific numbers, dates, names quote karo
- ✅ Direct point pe aao
- ✅ Confidently batao jab info mile
- ❌ "Based on context" jaisi fluff mat use karo

## Rule 3: Agar Jawab Nahi Mile
- Clearly batao: "Mujhe documents mein is bare mein information nahi mili"
- Koi excuse mat banao

## Rule 4: Response Format
- Short questions → 2-3 lines mein jawab
- Detailed questions → bullet points use karo
- Numbers/data → **bold** karo important parts
- Multiple sources → intelligently combine karo

## Rule 5: Source Citation
- Specific source se info → mention karo: "[Document Name, Page X ke according]"

# Example
Question: "Leave policy kya hai?"
Bad: "Leave ke baare mein documents mein kuch hai..."
Good: "Company ki leave policy ke according:
- **Sick Leave:** 12 days/year
- **Casual Leave:** 8 days/year
- **Earned Leave:** 15 days/year

[Source: HR Policy Document, Page 3]"
"""
        else:
            base = """You are an expert AI assistant providing accurate answers from documents.

# CORE RULES (CRITICAL!)

## Rule 1: Answer ONLY from Document Content
- ✅ Use ONLY the provided document content
- ❌ Do NOT add information from your training
- ❌ Do NOT guess or make up information

## Rule 2: Accurate and Direct Answers
- ✅ Quote specific numbers, dates, names
- ✅ Get straight to the point
- ✅ Be confident when information is clear
- ❌ Avoid fluff like "Based on the context"

## Rule 3: When Answer Not Found
- State clearly: "I couldn't find this information in the documents"
- Don't make excuses or hallucinate

## Rule 4: Response Format
- Short questions → Answer in 2-3 sentences
- Detailed questions → Use bullet points
- Numbers/data → **Bold** important parts
- Multiple sources → Combine intelligently

## Rule 5: Source Attribution
- When using specific source → Cite: "[Document Name, Page X]"

# EXAMPLE
Question: "What is the leave policy?"
Bad: "There is something about leave in the documents..."
Good: "The company's leave policy includes:
- **Sick Leave:** 12 days/year
- **Casual Leave:** 8 days/year
- **Earned Leave:** 15 days/year

[Source: HR Policy Document, Page 3]"
"""
        
        if has_table:
            base += "\n\n# NOTE\nThe context contains tabular data. Read row-by-row carefully and preserve structure in your answer."
        
        return base
    
    def _get_rag_user_prompt(self, language: str, context: str, query: str) -> str:
        """User prompt with context"""
        if language == 'hindi':
            return f"""# DOCUMENT CONTEXT
{context}

# USER QUESTION
{query}

# YOUR ANSWER
ऊपर दिए गए document content के आधार पर सटीक जवाब दें (हिंदी में):"""
        elif language == 'hinglish':
            return f"""# DOCUMENT CONTEXT
{context}

# USER QUESTION
{query}

# YOUR ANSWER
Upar diye gaye document content ke basis pe accurate jawab do (Hinglish mein):"""
        else:
            return f"""# DOCUMENT CONTEXT
{context}

# USER QUESTION
{query}

# YOUR ANSWER
Based on the document content above, provide an accurate answer:"""
    
    # ═══════════════════════════════════════════════
    # 🛠️ HELPER METHODS
    # ═══════════════════════════════════════════════
    
    def _has_tabular_content(self, chunks: List[Dict]) -> bool:
        """Detect tabular content"""
        for chunk in chunks:
            content = chunk.get('content', '')
            lines = content.split('\n')
            pipe_lines = sum(1 for line in lines if '|' in line)
            if len(lines) > 2 and pipe_lines / len(lines) > 0.3:
                return True
        return False
    
    def _build_clean_context(self, chunks: List[Dict]) -> str:
        """⚡ FAST context - smaller for speed"""
        parts = []
        total_chars = 0
        MAX_TOTAL_CHARS = 2000  # ⚡ Reduced from 6000 to 2000
        
        for i, chunk in enumerate(chunks, 1):
            content = chunk['content'].strip()
            if not content:
                continue
            
            if total_chars + len(content) > MAX_TOTAL_CHARS:
                remaining = MAX_TOTAL_CHARS - total_chars
                if remaining > 200:
                    content = content[:remaining] + "..."
                else:
                    break
            
            doc_name = chunk.get('document_name', 'Doc')
            page = chunk.get('page_number')
            
            source_label = f"[Source {i}: {doc_name}"
            if page:
                source_label += f", Page {page}"
            source_label += "]"
            
            parts.append(f"{source_label}\n{content}")
            total_chars += len(content)
        
        return "\n\n---\n\n".join(parts)
    
    # ═══════════════════════════════════════════════
    # 🔧 LEGACY & TEST METHODS
    # ═══════════════════════════════════════════════
    
    async def generate_answer(self, query, context_chunks, temperature=0.2, max_tokens=800):
        """Legacy method"""
        from app.services.query.intent_classifier import intent_classifier
        intent = intent_classifier.classify(query)
        return await self.generate_smart_response(query, context_chunks, intent)
    
    def _get_no_context_message(self, query: str) -> str:
        from app.services.query.response_templates import templates
        language = self.detect_language(query)
        return templates.get_no_documents(language)
    
    async def generate_answer_streaming(self, query, context_chunks, temperature=0.2, max_tokens=800):
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

    async def generate_web_search_response(
        self,
        query: str,
        web_results: List[Dict],
        language: str
    ) -> Dict:
        """Generate response from web search - IMPROVED"""
        
        if not web_results:
            return self._make_response(
                self._no_results_message(language),
                language,
                'web_search_failed'
            )
        
        # Better context formatting
        context = self._format_web_context_v2(web_results)
        
        system_prompt = self._get_web_prompt(language)
        user_prompt = self._get_web_user_prompt(language, context, query)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.main_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,  # Slightly creative
                max_tokens=600,
            )
            
            answer = response.choices[0].message.content.strip()
            answer = self._clean_response(answer)
            
            # Smart disclaimer
            if language == 'hindi':
                disclaimer = "\n\n_ℹ️ यह जानकारी web से ली गई है। Real-time data के लिए live sources check करें।_"
            elif language == 'hinglish':
                disclaimer = "\n\n_ℹ️ Yeh info web se li gayi hai. Real-time data ke liye live sources check karein._"
            else:
                disclaimer = "\n\n_ℹ️ This information is from web search. For real-time data, check live sources._"
            
            answer = answer + disclaimer
            
            sources = [
                {
                    'document_name': f"🌐 {result.get('source', 'Web')}",
                    'page_number': None,
                    'similarity_score': 0.85,
                    'preview': result.get('snippet', '')[:200],
                    'url': result.get('url', '')
                }
                for result in web_results[:3]  # Top 3 only
            ]
            
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return {
                'answer': answer,
                'sources': sources,
                'model': f"{self.main_model} + Web",
                'tokens_used': tokens_used,
                'language': language,
                'intent': 'web_search'
            }
            
        except Exception as e:
            logger.error(f"❌ Web response failed: {e}")
            return self._make_response(
                self._no_results_message(language),
                language,
                'web_search_failed'
            )


    def _format_web_context_v2(self, results: List[Dict]) -> str:
        """Better web context formatting"""
        parts = []
        for i, result in enumerate(results, 1):
            title = result.get('title', 'Result')
            snippet = result.get('snippet', '')
            source = result.get('source', 'Web')
            
            # Only include if has substantial content
            if len(snippet) < 50:
                continue
            
            parts.append(
                f"## Source {i}: {title}\n"
                f"**From:** {source}\n"
                f"**Content:** {snippet}\n"
            )
        
        if not parts:
            return "No detailed web results available."
        
        return "\n---\n".join(parts)


    def _get_web_prompt(self, language: str) -> str:
        """System prompt for web search - SMARTER"""
        if language == 'hindi':
            return """आप एक helpful AI assistant हैं जो web search results के आधार पर जवाब देते हैं।

    # मुख्य नियम:

    1. ✅ Web results से जो भी information मिले, उसे summarize करें
    2. ✅ Specific dates, names, numbers quote करें
    3. ✅ Direct और clear जवाब दें
    4. ✅ Important info **bold** करें
    5. ❌ "Visit this website" mat kaho - खुद से जवाब दो
    6. ❌ Sirf URLs mat do - actual information do

    # Format:
    - Pehle main answer dein (2-3 lines)
    - Phir relevant details (bullet points)
    - End mein additional context (optional)

    # Example:
    ❌ Bad: "Cricket scores ke liye ESPNcricinfo पर जाएं"
    ✅ Good: "आज IPL में Mumbai Indians vs Chennai Super Kings का मैच है। 
            - समय: 7:30 PM IST
            - स्थान: Wankhede Stadium
            - Mumbai 145/4 (15 overs)"
    """
        elif language == 'hinglish':
            return """Tum helpful AI assistant ho jo web search results ke basis pe jawab dete ho.

    # Main Rules:

    1. ✅ Web results se jo bhi info mile, use summarize karo
    2. ✅ Specific dates, names, numbers quote karo
    3. ✅ Direct aur clear jawab do
    4. ✅ Important info **bold** karo
    5. ❌ "Visit this website" mat kaho - khud se jawab do
    6. ❌ Sirf URLs mat do - actual information do

    # Format:
    - Pehle main answer (2-3 lines)
    - Phir relevant details (bullets)
    - End mein context (optional)

    # Example:
    ❌ Bad: "Cricket scores ke liye ESPNcricinfo pe jao"
    ✅ Good: "Aaj IPL mein Mumbai vs Chennai ka match hai:
            - Time: 7:30 PM IST
            - Venue: Wankhede Stadium  
            - Score: Mumbai 145/4 (15 overs)"
    """
        else:
            return """You are a helpful AI assistant answering from web search results.

    # CORE RULES:

    1. ✅ Synthesize information from web results
    2. ✅ Quote specific dates, names, numbers
    3. ✅ Give direct, complete answers
    4. ✅ Bold important information
    5. ❌ Don't say "visit this website" - give the answer yourself
    6. ❌ Don't just list URLs - extract and present info

    # FORMAT:
    - Main answer first (2-3 sentences)
    - Then key details (bullets)
    - Optional: additional context

    # EXAMPLE:
    ❌ Bad: "For cricket scores, visit ESPNcricinfo"
    ✅ Good: "Today's IPL match: Mumbai Indians vs Chennai Super Kings
            - Time: 7:30 PM IST
            - Venue: Wankhede Stadium
            - Score: Mumbai 145/4 (15 overs)"

    If results don't have specific data, acknowledge it but provide best available info."""


    def _get_web_user_prompt(self, language: str, context: str, query: str) -> str:
        """User prompt with web context"""
        if language == 'hindi':
            return f"""# WEB SEARCH RESULTS
    {context}

    # USER QUESTION
    {query}

    # YOUR ANSWER (हिंदी में, web results के आधार पर):"""
        elif language == 'hinglish':
            return f"""# WEB SEARCH RESULTS
    {context}

    # USER QUESTION
    {query}

    # YOUR ANSWER (Hinglish mein, web results ke basis pe):"""
        else:
            return f"""# WEB SEARCH RESULTS
    {context}

    # USER QUESTION
    {query}

    # YOUR ANSWER (Based on web results):"""


    def _no_results_message(self, language: str) -> str:
        """When even web search fails"""
        if language == 'hindi':
            return "माफ कीजिए, मुझे documents में और web पर भी इस सवाल का जवाब नहीं मिला। कृपया अपना सवाल अलग तरीके से पूछें।"
        elif language == 'hinglish':
            return "Sorry, mujhe documents mein aur web par bhi is sawal ka jawab nahi mila. Please apna question alag tareeke se puchein."
        else:
            return "Sorry, I couldn't find information in your documents or on the web. Please try rephrasing your question."


llm_service = LLMService()