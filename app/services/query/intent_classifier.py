"""
SUPER Smart Intent Classification Service
Detects 20+ intents for natural conversation
"""
import re
from datetime import datetime
from typing import Dict, Optional
from app.utils import logger


class IntentClassifier:
    """Comprehensive intent classifier for natural conversations"""
    
    # ─── GREETINGS ───
    GREETINGS_EN = {
        'hi', 'hii', 'hiii', 'hiiii', 'hello', 'helo', 'hlo', 'hii there',
        'hey', 'heyy', 'heyyy', 'hai', 'haii', 'hellow',
        'howdy', 'greetings', 'sup', 'wassup', 'whats up', "what's up",
        'yo', 'yoo', 'hola', 'salam', 'salaam',
    }
    
    GREETINGS_HI = {
        'namaste', 'namaskar', 'namaskaar', 'pranam', 'pranaam',
        'नमस्ते', 'नमस्कार', 'प्रणाम', 'सलाम',
        'ram ram', 'jai shree krishna', 'jai shri ram', 'radhe radhe',
    }
    
    # ─── TIME-BASED GREETINGS ───
    MORNING_GREETINGS = {
        'good morning', 'gm', 'gud morning', 'goodmorning', 'morning',
        'suprabhat', 'suprabhaat', 'सुप्रभात', 'शुभ प्रभात',
        'subah ki shubhkamnaye',
    }
    
    AFTERNOON_GREETINGS = {
        'good afternoon', 'ga', 'gud afternoon',
        'shubh dophar', 'शुभ दोपहर',
    }
    
    EVENING_GREETINGS = {
        'good evening', 'ge', 'gud evening',
        'shubh sandhya', 'शुभ संध्या', 'शुभ शाम',
    }
    
    NIGHT_GREETINGS = {
        'good night', 'gn', 'gud night', 'goodnight', 'nighty night',
        'shubh ratri', 'शुभ रात्रि', 'shabba khair',
    }
    
    # ─── HOW ARE YOU ───
    HOW_ARE_YOU = {
        'how are you', 'how r u', 'hru', 'how are u', 'how you doing',
        'how do you do', 'how r you',
        'kaise ho', 'kaise hain', 'kaisi ho', 'kaisi hain',
        'kaise hain aap', 'kaise ho tum', 'kya haal', 'kya hal',
        'kya hal hai', 'kya haal hai', 'kya haal chal',
        'kaisa hai', 'kaisa hain', 'sab badhiya', 'sab theek',
        'कैसे हो', 'कैसे हैं', 'कैसी हो', 'कैसी हैं',
        'क्या हाल', 'क्या हाल है', 'सब ठीक', 'क्या चल रहा',
    }
    
    # ─── FAREWELLS ───
    FAREWELLS = {
        'bye', 'bbye', 'byebye', 'goodbye', 'good bye', 'cya', 'see ya',
        'see you', 'see u', 'see u later', 'see you later', 'later',
        'take care', 'tc', 'catch you later',
        'tata', 'ta ta', 'alvida', 'phir milenge', 'phir milte hain',
        'अलविदा', 'फिर मिलेंगे', 'फिर मिलते हैं', 'टाटा',
    }
    
    # ─── THANKS ───
    THANKS = {
        'thanks', 'thank you', 'thanku', 'thnk u', 'thankyou', 'thx', 'tnx',
        'ty', 'tysm', 'thanks a lot', 'thanks alot', 'thank u so much',
        'much appreciated', 'appreciate it', 'thanks bro', 'thanks bhai',
        'dhanyavad', 'dhanyavaad', 'shukriya', 'shukran',
        'धन्यवाद', 'शुक्रिया', 'thanks yaar',
    }
    
    # ─── HELP REQUESTS ───
    HELP_KEYWORDS = {
        'help', 'help me', 'madad', 'mdd', 'sahayata', 'मदद', 'सहायता',
        'what can you do', 'what do you do', 'how does this work',
        'capabilities', 'features', 'kya kar sakte ho', 'kya kr sakte ho',
        'how to use', 'how do i use', 'kaise use karu', 'kaise istemal',
        'guide me', 'show me how', 'instructions', 'kaise chalu',
    }
    
    # ─── IDENTITY ───
    IDENTITY_KEYWORDS = {
        'who are you', 'what are you', 'who r u', 'who is this',
        'tum kaun ho', 'aap kaun ho', 'ye kaun', 'kaun ho tum',
        'your name', 'whats your name', "what's your name", 'tumhara naam',
        'aapka naam', 'tera naam', 'kya naam', 'introduce yourself',
        'introduce', 'about you', 'tell me about yourself',
        'तुम कौन हो', 'आप कौन हो', 'तुम्हारा नाम', 'आपका नाम',
    }
    
    # ─── COMPLIMENTS ───
    COMPLIMENTS = {
        'good bot', 'great bot', 'nice bot', 'smart bot', 'cool bot',
        'awesome', 'amazing', 'fantastic', 'excellent', 'brilliant',
        'great', 'great work', 'good work', 'well done', 'nice work',
        'perfect', 'wonderful', 'superb', 'impressive',
        'you are smart', 'you are great', 'you are good', 'youre smart',
        "you're smart", "you're good", "you're great", "you're awesome",
        'bahut accha', 'bahut acha', 'mast', 'badhiya', 'shandar',
        'kamaal', 'jhakkas', 'lajawab', 'wah', 'waah',
        'बहुत अच्छा', 'शानदार', 'कमाल', 'बढ़िया', 'जबरदस्त',
        'tum smart ho', 'tum acche ho', 'aap smart ho',
    }
    
    # ─── COMPLAINTS / NEGATIVE ───
    COMPLAINTS = {
        'bad', 'terrible', 'awful', 'worst', 'useless', 'stupid',
        'you are stupid', 'you are dumb', 'youre stupid', "you're stupid",
        'bekar', 'bekaar', 'bakwas', 'bakwaas', 'bekarr',
        'kuch nhi pata', 'kuch nahi pata', 'galat hai', 'wrong',
        'incorrect', 'not helpful', 'useless bot',
        'बेकार', 'बकवास', 'गलत',
    }
    
    # ─── EMOTIONS ───
    SAD_EXPRESSIONS = {
        'i am sad', 'im sad', "i'm sad", 'feeling sad', 'feeling low',
        'depressed', 'upset', 'crying', 'heartbroken',
        'mai udaas hu', 'main udaas hun', 'dukhi hu', 'dukhi hun',
        'mood off', 'mood kharab', 'pareshan hu', 'pareshan hun',
        'मैं उदास हूं', 'दुखी हूं', 'परेशान हूं',
    }
    
    HAPPY_EXPRESSIONS = {
        'i am happy', 'im happy', "i'm happy", 'feeling great',
        'feeling good', 'excited', 'thrilled', 'awesome day',
        'mai khush hu', 'main khush hun', 'bahut khush',
        'mood acha', 'mood good', 'mast feel',
        'मैं खुश हूं', 'बहुत खुश',
    }
    
    TIRED_EXPRESSIONS = {
        'i am tired', 'im tired', "i'm tired", 'so tired', 'exhausted',
        'sleepy', 'feeling sleepy',
        'thak gaya', 'thak gayi', 'thaka hua', 'neend aa rahi',
        'थक गया', 'थकी हूं', 'नींद आ रही',
    }
    
    BORED_EXPRESSIONS = {
        'i am bored', 'im bored', "i'm bored", 'so bored', 'boring',
        'bore ho raha', 'bore ho rahi', 'bore hu', 'bore hun',
        'boring hai', 'kuch interesting',
        'बोर हो रहा', 'बोर हूं',
    }
    
    # ─── CASUAL CHAT ───
    WHAT_DOING = {
        'what are you doing', 'whatre you doing', "what're you doing",
        'wyd', 'kya kar rahe ho', 'kya kr rahe ho', 'kya kar rhe ho',
        'kya kr rhe ho', 'kya karte ho', 'kya bana rahe',
        'क्या कर रहे हो', 'क्या कर रहे हैं',
    }
    
    BUSY_QUESTIONS = {
        'are you busy', 'busy ho', 'free ho', 'are you free',
        'व्यस्त हो', 'फ्री हो',
    }
    
    # ─── APPROVALS ───
    APPROVALS = {
        'ok', 'okay', 'okk', 'okkk', 'oki', 'k', 'kk',
        'theek hai', 'thik hai', 'thik h', 'theek h', 'tk',
        'sahi', 'sahi hai', 'sahi h', 'correct', 'right',
        'haan', 'haa', 'han', 'yes', 'yess', 'yep', 'yeah', 'yup',
        'samjha', 'samjhi', 'samjh gaya', 'samjh gayi', 'got it',
        'understood', 'acha', 'accha', 'acchaa', 'achha',
        'ठीक है', 'सही', 'हाँ', 'समझा', 'समझ गया', 'अच्छा',
    }
    
    REJECTIONS = {
        'no', 'nope', 'nah', 'na', 'nahi', 'nahin', 'nhi',
        'not really', 'not interested', 'cancel', 'rehne do',
        'नहीं', 'नही',
    }
    
    # ─── CONFUSION ───
    CONFUSION = {
        'what', 'wat', 'whaat', 'kya', 'kyaa', 'kya bola',
        'samjha nahi', 'samjhi nahi', 'samajh nahi aaya',
        'i dont understand', "i don't understand", 'didnt understand',
        "didn't understand", 'confused', 'confuse ho gaya',
        'repeat', 'phir se bolo', 'dobara bolo', 'fir bolo',
        'samjhao', 'explain again', 'kya matlab', 'matlab',
        'क्या', 'समझा नहीं', 'समझ नहीं आया', 'फिर से बोलो',
    }
    
    # ─── JOKES ───
    JOKE_REQUESTS = {
        'tell me a joke', 'joke sunao', 'koi joke', 'ek joke',
        'make me laugh', 'hasao mujhe', 'funny joke', 'something funny',
        'joke bolo', 'mazak', 'चुटकुला', 'मज़ाक',
    }
    
    # ─── TIME/DATE ───
    TIME_QUESTIONS = {
        'what time', 'whats the time', "what's the time", 'time kya',
        'time hua', 'kitne baje', 'samay kya',
        'क्या समय', 'कितने बजे', 'समय',
    }
    
    DATE_QUESTIONS = {
        'whats the date', "what's the date", 'what date', 'aaj ki date',
        'aaj date kya', 'tarikh kya', 'kaun sa din',
        'what day', 'which day', 'aaj kaunsa din',
        'क्या तारीख', 'कौन सा दिन',
    }
    
    # ─── TRANSLATION ───
    TRANSLATION_PATTERNS = [
        r'translate\s+(?:to|in|into)\s+\w+\s*:?\s*(.+)',
        r'translate\s+(.+)\s+(?:to|in|into)\s+(\w+)',
        r'(\w+)\s+(?:mein|me)\s+(.+)\s+(?:kya|kaise)',
        r'meaning of\s+(.+)',
        r'(.+)\s+meaning',
        r'(.+)\s+ka matlab',
        r'(.+)\s+का मतलब',
        r'how do you say\s+(.+)',
        r'how to say\s+(.+)',
    ]
    
    # ─── MATH ───
    MATH_PATTERNS = [
        r'\d+\s*[\+\-\*\/x×÷]\s*\d+',
        r'calculate\s+',
        r'what is\s+\d+',
        r'how much is\s+',
        r'\d+\s*plus\s*\d+',
        r'\d+\s*minus\s*\d+',
        r'\d+\s*times\s*\d+',
    ]
    
    # ─── DOCUMENT KEYWORDS ───
    DOCUMENT_KEYWORDS = {
        'document', 'pdf', 'file', 'documents', 'docs', 'paper',
        'in the doc', 'from the doc', 'in document', 'from document',
        'mentioned in', 'according to', 'based on', 'as per',
        'mere documents', 'documents mein', 'pdf mein', 'file mein',
        'दस्तावेज़', 'फाइल', 'पीडीएफ',
        'summarize', 'summary', 'overview', 'main points', 'key points',
        'list', 'extract', 'find', 'search', 'tell me about',
        'leave', 'policy', 'rule', 'rules', 'company',
        'employee', 'salary', 'office', 'timing', 'working',
        'kitne', 'kitna', 'kitni', 'kyun', 'kaise',
    }
    
    @classmethod
    def get_time_period(cls) -> str:
        """Get current time period for time-based greetings"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    @classmethod
    def classify(cls, query: str) -> Dict:
        """
        Comprehensive intent classification
        
        Returns:
            {
                'intent': str,
                'use_rag': bool,
                'confidence': float,
                'language_hint': str,
                'response_type': str,
                'metadata': dict (optional)
            }
        """
        if not query or not query.strip():
            return cls._default_response()
        
        query_lower = query.lower().strip()
        query_clean = re.sub(r'[^\w\s]', '', query_lower).strip()
        words = query_clean.split()
        word_count = len(words)
        
        # Language detection
        has_hindi = bool(re.search(r'[\u0900-\u097F]', query))
        language_hint = cls._detect_language(query, has_hindi)
        
        # ─── TIME-BASED GREETINGS (Check FIRST!) ───
        if cls._matches_any(query_clean, cls.MORNING_GREETINGS):
            return cls._make_intent('morning_greeting', False, 0.95, language_hint, 'direct')
        
        if cls._matches_any(query_clean, cls.AFTERNOON_GREETINGS):
            return cls._make_intent('afternoon_greeting', False, 0.95, language_hint, 'direct')
        
        if cls._matches_any(query_clean, cls.EVENING_GREETINGS):
            return cls._make_intent('evening_greeting', False, 0.95, language_hint, 'direct')
        
        if cls._matches_any(query_clean, cls.NIGHT_GREETINGS):
            return cls._make_intent('night_greeting', False, 0.95, language_hint, 'direct')
        
        # ─── HOW ARE YOU ───
        if cls._matches_any(query_clean, cls.HOW_ARE_YOU):
            return cls._make_intent('how_are_you', False, 0.95, language_hint, 'direct')
        
        # ─── GREETINGS ───
        if cls._is_greeting(query_clean, words, word_count):
            return cls._make_intent('greeting', False, 0.95, language_hint, 'direct')
        
        # ─── FAREWELLS ───
        if cls._matches_any(query_clean, cls.FAREWELLS) and word_count <= 4:
            return cls._make_intent('farewell', False, 0.9, language_hint, 'direct')
        
        # ─── THANKS ───
        if cls._matches_any(query_clean, cls.THANKS):
            return cls._make_intent('thanks', False, 0.9, language_hint, 'direct')
        
        # ─── COMPLIMENTS ───
        if cls._matches_any(query_clean, cls.COMPLIMENTS):
            return cls._make_intent('compliment', False, 0.85, language_hint, 'direct')
        
        # ─── COMPLAINTS ───
        if cls._matches_any(query_clean, cls.COMPLAINTS) and word_count <= 6:
            return cls._make_intent('complaint', False, 0.8, language_hint, 'direct')
        
        # ─── EMOTIONS ───
        if cls._matches_any(query_clean, cls.SAD_EXPRESSIONS):
            return cls._make_intent('sad_emotion', False, 0.85, language_hint, 'direct')
        
        if cls._matches_any(query_clean, cls.HAPPY_EXPRESSIONS):
            return cls._make_intent('happy_emotion', False, 0.85, language_hint, 'direct')
        
        if cls._matches_any(query_clean, cls.TIRED_EXPRESSIONS):
            return cls._make_intent('tired_emotion', False, 0.85, language_hint, 'direct')
        
        if cls._matches_any(query_clean, cls.BORED_EXPRESSIONS):
            return cls._make_intent('bored_emotion', False, 0.85, language_hint, 'direct')
        
        # ─── CASUAL CHAT ───
        if cls._matches_any(query_clean, cls.WHAT_DOING):
            return cls._make_intent('what_doing', False, 0.85, language_hint, 'direct')
        
        if cls._matches_any(query_clean, cls.BUSY_QUESTIONS):
            return cls._make_intent('busy_question', False, 0.85, language_hint, 'direct')
        
        # ─── APPROVALS/REJECTIONS (only if very short) ───
        if word_count <= 3 and cls._matches_any(query_clean, cls.APPROVALS):
            return cls._make_intent('approval', False, 0.9, language_hint, 'direct')
        
        if word_count <= 3 and cls._matches_any(query_clean, cls.REJECTIONS):
            return cls._make_intent('rejection', False, 0.9, language_hint, 'direct')
        
        # ─── CONFUSION ───
        if cls._matches_any(query_clean, cls.CONFUSION) and word_count <= 5:
            return cls._make_intent('confusion', False, 0.85, language_hint, 'direct')
        
        # ─── JOKES ───
        if cls._matches_any(query_clean, cls.JOKE_REQUESTS):
            return cls._make_intent('joke_request', False, 0.9, language_hint, 'llm_direct')
        
        # ─── TIME/DATE ───
        if cls._matches_any(query_clean, cls.TIME_QUESTIONS):
            return cls._make_intent('time_question', False, 0.9, language_hint, 'direct')
        
        if cls._matches_any(query_clean, cls.DATE_QUESTIONS):
            return cls._make_intent('date_question', False, 0.9, language_hint, 'direct')
        
        # ─── HELP ───
        if cls._matches_any(query_clean, cls.HELP_KEYWORDS):
            return cls._make_intent('help', False, 0.9, language_hint, 'direct')
        
        # ─── IDENTITY ───
        if cls._matches_any(query_clean, cls.IDENTITY_KEYWORDS):
            return cls._make_intent('identity', False, 0.9, language_hint, 'direct')
        
        # ─── TRANSLATION ───
        if cls._is_translation(query_lower):
            return cls._make_intent('translation', False, 0.85, language_hint, 'llm_direct')
        
        # ─── MATH ───
        if cls._is_math(query_lower):
            return cls._make_intent('math', False, 0.85, language_hint, 'llm_direct')
        
        # ─── DOCUMENT QUERY ───
        if cls._is_document_query(query_lower, word_count):
            return cls._make_intent('document_query', True, 0.85, language_hint, 'rag')
        
        # ─── DEFAULT: Document query for meaningful questions ───
        if word_count >= 3:
            return cls._make_intent('document_query', True, 0.6, language_hint, 'rag')
        
        # Short queries = general chat
        return cls._make_intent('general_chat', False, 0.5, language_hint, 'llm_direct')
    
    @classmethod
    def _matches_any(cls, query: str, keyword_set: set) -> bool:
        """Check if query matches any keyword"""
        # Exact match
        if query in keyword_set:
            return True
        
        # Check if any keyword is in query
        for keyword in keyword_set:
            if keyword in query:
                # Make sure it's a word boundary (not part of larger word)
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, query):
                    return True
        
        return False
    
    @classmethod
    def _is_greeting(cls, query: str, words: list, word_count: int) -> bool:
        """Check generic greetings"""
        if word_count > 5:
            return False
        
        if query in cls.GREETINGS_EN or query in cls.GREETINGS_HI:
            return True
        
        if words and words[0] in cls.GREETINGS_EN:
            return True
        
        for greeting in cls.GREETINGS_HI:
            if greeting in query:
                return True
        
        return False
    
    @classmethod
    def _is_translation(cls, query: str) -> bool:
        """Check translation"""
        for pattern in cls.TRANSLATION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        keywords = ['translate', 'meaning', 'matlab', 'मतलब', 'अर्थ']
        for keyword in keywords:
            if keyword in query:
                return True
        
        return False
    
    @classmethod
    def _is_math(cls, query: str) -> bool:
        """Check math"""
        for pattern in cls.MATH_PATTERNS:
            if re.search(pattern, query):
                return True
        return False
    
    @classmethod
    def _is_document_query(cls, query: str, word_count: int) -> bool:
        """Check document query"""
        for keyword in cls.DOCUMENT_KEYWORDS:
            if keyword in query:
                return True
        
        question_patterns = [
            r'^(what|who|when|where|why|how|which|whose)\s',
            r'^(kya|kaun|kab|kahan|kyu|kyun|kaise|kis|kitne|kitna)\s',
            r'^(क्या|कौन|कब|कहाँ|क्यों|कैसे|किस|कितने)\s',
            r'tell me about',
            r'explain\s+',
            r'describe\s+',
            r'batao\s+',
            r'samjhao\s+',
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, query):
                return word_count >= 3
        
        return False
    
    @classmethod
    def _detect_language(cls, query: str, has_hindi: bool) -> str:
        """Detect language"""
        if has_hindi:
            return 'hindi'
        
        hinglish_keywords = [
            'kya', 'kaun', 'kahan', 'kab', 'kaise', 'kyun', 'kyu',
            'hai', 'hain', 'tha', 'thi', 'ho', 'hoga',
            'mera', 'meri', 'tera', 'teri', 'aap', 'tum',
            'batao', 'bata', 'chahiye', 'karna', 'karo',
            'mujhe', 'tujhe', 'acha', 'accha', 'theek',
            'nahi', 'nahin', 'haan', 'han', 'bhai', 'yaar',
            'kitne', 'sakta', 'sakte', 'leave',
        ]
        
        text_lower = query.lower()
        count = sum(1 for word in hinglish_keywords if re.search(r'\b' + word + r'\b', text_lower))
        
        if count >= 2:
            return 'hinglish'
        if count >= 1 and len(query.split()) < 8:
            return 'hinglish'
        
        return 'english'
    
    @classmethod
    def _make_intent(cls, intent: str, use_rag: bool, confidence: float, 
                     language: str, response_type: str) -> Dict:
        """Build intent dictionary"""
        return {
            'intent': intent,
            'use_rag': use_rag,
            'confidence': confidence,
            'language_hint': language,
            'response_type': response_type,
        }
    
    @classmethod
    def _default_response(cls) -> Dict:
        """Default classification"""
        return cls._make_intent('general_chat', False, 0.3, 'english', 'llm_direct')


# Global instance
intent_classifier = IntentClassifier()
