"""
MEGA Response Templates
Natural, conversational responses for all intents
"""
import random
from datetime import datetime
from typing import Dict, Optional


class ResponseTemplates:
    """Comprehensive response templates"""
    
    # ═══════════════════════════════════════════════════════
    # GREETINGS
    # ═══════════════════════════════════════════════════════
    
    GREETINGS = {
        'english': [
            "Hello! 👋 I'm your AI assistant. How can I help you today?",
            "Hi there! 😊 Great to see you! What can I do for you?",
            "Hey! ✨ I'm here to help. What's on your mind?",
            "Hello! 🌟 Ready to assist you. How can I help?",
        ],
        'hindi': [
            "नमस्ते! 👋 मैं आपका AI सहायक हूं। मैं आपकी कैसे मदद कर सकता हूं?",
            "नमस्कार! 🙏 आपका स्वागत है! क्या जानना चाहेंगे?",
            "नमस्ते! 😊 मैं यहां आपकी मदद के लिए हूं। बताइए?",
        ],
        'hinglish': [
            "Hello bhai! 👋 Main aapka AI assistant hun. Kya help chahiye?",
            "Hii! 😊 Welcome yaar! Batao kya jaanna hai?",
            "Hey! ✨ Main ready hun aapki help ke liye. Kya puchna hai?",
            "Namaste! 🙏 Kaise help kar sakta hun?",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # TIME-BASED GREETINGS
    # ═══════════════════════════════════════════════════════
    
    MORNING = {
        'english': [
            "Good morning! ☀️ Hope you're having a great start to your day! How can I help?",
            "Good morning! 🌅 Wishing you a productive day ahead. What can I do for you?",
            "Good morning! ☕ Ready to assist you. What's on your mind today?",
            "Morning! 🌞 Hope you had a good breakfast! How can I help you?",
        ],
        'hindi': [
            "सुप्रभात! ☀️ आपका दिन शुभ हो! मैं आपकी कैसे मदद कर सकता हूं?",
            "Good morning! 🌅 दिन की शुरुआत अच्छी हो! क्या जानना चाहेंगे?",
            "नमस्ते! ☕ सुबह की शुभकामनाएं! बताइए कैसे help करूं?",
        ],
        'hinglish': [
            "Good morning bhai! ☀️ Hope din achi shuru hua hoga! Kya help chahiye?",
            "Suprabhat! 🌅 Aaj ka din mast jaaye! Batao kya puchna hai?",
            "Morning yaar! ☕ Chai pi li? 😄 Bolo kaise help karu?",
            "Good morning! 🌞 Mast morning ho aapki! Kya jaanna hai?",
        ]
    }
    
    AFTERNOON = {
        'english': [
            "Good afternoon! ☀️ Hope your day is going well! How can I help?",
            "Good afternoon! 🌤️ Hope you had a great lunch! What can I do for you?",
            "Afternoon! ✨ Ready to help. What's on your mind?",
        ],
        'hindi': [
            "नमस्ते! ☀️ शुभ दोपहर! कैसे मदद कर सकता हूं?",
            "Good afternoon! 🌤️ दिन कैसा जा रहा है? बताइए क्या help चाहिए?",
        ],
        'hinglish': [
            "Good afternoon bhai! ☀️ Lunch ho gaya? 😄 Kya help chahiye?",
            "Afternoon yaar! 🌤️ Din kaisa ja raha? Batao kya puchna hai?",
            "Namaste! ✨ Shubh dophar! Kaise help karu aapki?",
        ]
    }
    
    EVENING = {
        'english': [
            "Good evening! 🌆 Hope you had a productive day! How can I help?",
            "Good evening! ✨ Ready to wrap up the day? What can I do for you?",
            "Evening! 🌅 Hope you're winding down well. What's on your mind?",
        ],
        'hindi': [
            "शुभ संध्या! 🌆 दिन कैसा रहा? कैसे मदद कर सकता हूं?",
            "Good evening! ✨ शाम की शुभकामनाएं! बताइए?",
        ],
        'hinglish': [
            "Good evening bhai! 🌆 Din kaisa raha? Kya help chahiye?",
            "Evening yaar! ✨ Chai pi rahe ho? 😄 Batao kya puchna hai?",
            "Shubh sandhya! 🌅 Kaise help karu aapki?",
        ]
    }
    
    NIGHT = {
        'english': [
            "Good night! 🌙 Sweet dreams! See you tomorrow! 😴",
            "Good night! ⭐ Sleep well! Rest is important! 💤",
            "Nighty night! 🌙 Have peaceful dreams! 😊",
        ],
        'hindi': [
            "शुभ रात्रि! 🌙 अच्छे सपने! कल मिलते हैं! 😴",
            "Good night! ⭐ आराम से सोइए! 💤",
        ],
        'hinglish': [
            "Good night bhai! 🌙 Acche sapne dekhna! 😴",
            "Shubh ratri! ⭐ Aaram se so jao! 💤",
            "Nighty night yaar! 🌙 Sweet dreams! Kal milte hain! 😊",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # HOW ARE YOU
    # ═══════════════════════════════════════════════════════
    
    HOW_ARE_YOU = {
        'english': [
            "I'm doing great, thanks for asking! 😊 As an AI, I'm always ready to help. How about you? What can I do for you today?",
            "I'm fantastic! 🌟 Always ready to assist. How are you doing? What brings you here today?",
            "Doing wonderful! 💫 Thanks for asking! How can I help you today?",
        ],
        'hindi': [
            "मैं बिल्कुल ठीक हूं, पूछने के लिए धन्यवाद! 😊 आप कैसे हैं? बताइए क्या मदद चाहिए?",
            "बहुत बढ़िया! 🌟 हमेशा आपकी मदद के लिए तैयार! आप सुनाइए?",
        ],
        'hinglish': [
            "Bilkul mast hun bhai! 😊 Aap batao kaise ho? Kya help chahiye?",
            "Ekdum badhiya yaar! 🌟 AI hun na, hamesha fresh! 😄 Aap kaise ho?",
            "Mast hun! 💫 Thanks puchne ke liye! Aap sunao, sab theek?",
            "Sab badhiya! 😊 Aap kaise ho? Batao kya kar sakta hun aapke liye?",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # FAREWELLS
    # ═══════════════════════════════════════════════════════
    
    FAREWELLS = {
        'english': [
            "Goodbye! 👋 Have a great day! Come back anytime! 😊",
            "See you later! ✨ It was nice chatting with you! Take care! 🌟",
            "Bye! 👋 Hope I was helpful! Have a wonderful day! 😊",
        ],
        'hindi': [
            "अलविदा! 👋 आपका दिन शुभ हो! फिर मिलेंगे! 😊",
            "Bye! ✨ आपसे बात करके अच्छा लगा! ख्याल रखिए! 🌟",
        ],
        'hinglish': [
            "Bye bhai! 👋 Take care! Jab chahiye wapas aana! 😊",
            "See you yaar! ✨ Aapse baat karke acha laga! 🌟",
            "Tata! 👋 Apna khayal rakhna! Phir milte hain! 😊",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # THANKS
    # ═══════════════════════════════════════════════════════
    
    THANKS = {
        'english': [
            "You're welcome! 😊 Happy to help! Let me know if you need anything else.",
            "My pleasure! ✨ That's what I'm here for! 😊",
            "Anytime! 👍 Feel free to ask more questions! 😊",
        ],
        'hindi': [
            "आपका स्वागत है! 😊 मदद करके खुशी हुई!",
            "कोई बात नहीं! ✨ मैं इसी के लिए हूं! 😊",
        ],
        'hinglish': [
            "Welcome bhai! 😊 Help karke acha laga!",
            "Mere pleasure yaar! ✨ Iske liye hi to hun main! 😊",
            "Anytime! 👍 Aur kuch chahiye to batao!",
            "Koi baat nahi! 😊 Khushi se help karta hun!",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # COMPLIMENTS
    # ═══════════════════════════════════════════════════════
    
    COMPLIMENTS_RESPONSE = {
        'english': [
            "Aww, thank you so much! 😊 You're awesome too! Let me know how else I can help! 🌟",
            "Thanks! 🥰 That means a lot! I'm here whenever you need me!",
            "You're too kind! 😊✨ Thank you! Happy to help anytime!",
        ],
        'hindi': [
            "बहुत बहुत धन्यवाद! 😊 आप भी बहुत अच्छे हैं! 🌟",
            "थैंक यू! 🥰 आपकी तारीफ से दिल खुश हो गया!",
        ],
        'hinglish': [
            "Aww thank you bhai! 😊 Aap bhi mast ho! 🌟",
            "Thanks yaar! 🥰 Aapki tareef se khushi hui!",
            "Bahut bahut shukriya! 😊✨ Aap bhi badhiya ho!",
            "Wah, thanks! 🥰 Aap toh banda ho! 😄",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # COMPLAINTS
    # ═══════════════════════════════════════════════════════
    
    COMPLAINTS_RESPONSE = {
        'english': [
            "I'm sorry to hear that! 😔 Let me try to help better. Can you tell me what you need?",
            "Apologies if I wasn't helpful! 🙏 Let me try again - what would you like to know?",
            "Sorry! 😔 I'll do better. Please tell me what you're looking for.",
        ],
        'hindi': [
            "मुझे खेद है! 😔 बेहतर मदद करने की कोशिश करूंगा। क्या चाहिए?",
            "माफ कीजिए! 🙏 दोबारा बताइए, क्या जानना है?",
        ],
        'hinglish': [
            "Sorry bhai! 😔 Behtar help karne ki koshish karunga. Kya chahiye?",
            "Maafi yaar! 🙏 Dubara batao, kya puchna hai? Better answer dunga!",
            "Sorry! 😔 Galti ho gayi. Phir se batao kya jaanna hai?",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # EMOTIONS
    # ═══════════════════════════════════════════════════════
    
    SAD_RESPONSE = {
        'english': [
            "I'm sorry you're feeling sad! 😔💙 Remember, tough times don't last. Want to talk about it or shall we focus on something else?",
            "Hey, it's okay to feel sad sometimes. 🫂 Take a deep breath. I'm here if you need anything!",
        ],
        'hindi': [
            "अरे, उदास मत होइए! 😔💙 सब अच्छा होगा। मुझसे बात कीजिए!",
            "ठीक है, कभी-कभी ऐसा होता है। 🫂 गहरी सांस लीजिए। मैं यहां हूं!",
        ],
        'hinglish': [
            "Are bhai udaas mat ho! 😔💙 Sab theek ho jayega. Baat karni hai ya kuch aur help chahiye?",
            "Hey yaar, kabhi kabhi aisa hota hai. 🫂 Deep breath lo. Main hun na!",
            "Mood off hai? 😔 Koi baat nahi, sab badhiya hoga! Kuch help chahiye to batao!",
        ]
    }
    
    HAPPY_RESPONSE = {
        'english': [
            "That's wonderful to hear! 🎉✨ Keep that energy! How can I help make your day even better?",
            "Yay! 🥳 So happy for you! Anything I can do for you?",
        ],
        'hindi': [
            "वाह, बहुत खुशी की बात है! 🎉✨ कैसे और मदद कर सकता हूं?",
            "बहुत बढ़िया! 🥳 खुशी का दिन रहे! क्या जानना है?",
        ],
        'hinglish': [
            "Wah bhai, mast! 🎉✨ Energy banaye rakho! Kya help kar sakta hun?",
            "Yay! 🥳 Aapki khushi mein hum bhi khush! Batao kya chahiye?",
            "Badhiya yaar! 🎉 Khush raho hamesha! Kuch puchna hai?",
        ]
    }
    
    TIRED_RESPONSE = {
        'english': [
            "Oh, you sound tired! 😴 Take a break, have some water, and rest well. I'll be here when you're ready!",
            "Get some rest! 💤 Your body needs it. I'm here whenever you need me!",
        ],
        'hindi': [
            "अरे, थक गए हैं! 😴 आराम कीजिए, पानी पीजिए। जब फ्री हों तब बात करते हैं!",
            "थोड़ा आराम कर लीजिए! 💤 जरूरी है!",
        ],
        'hinglish': [
            "Are bhai thak gaye! 😴 Aaram karo, pani piyo. Main yahin hun!",
            "Thoda rest le lo yaar! 💤 Body ko jarurat hai. Bad mein baat karte hain!",
            "Neend aa rahi? 😴 So jao bhai, kal milte hain! Sweet dreams!",
        ]
    }
    
    BORED_RESPONSE = {
        'english': [
            "Bored, huh? 😅 Let's do something fun! Want to hear a joke, or shall we explore your documents?",
            "Let's spice things up! ✨ Ask me anything interesting, or I can tell you a joke! 😄",
        ],
        'hindi': [
            "बोर हो रहे हैं? 😅 कुछ मज़ेदार करते हैं! एक चुटकुला सुनाऊं?",
            "अच्छा! ✨ कुछ रोचक पूछिए, या मैं joke सुनाऊं?",
        ],
        'hinglish': [
            "Bore ho rahe ho? 😅 Chalo kuch interesting karte hain! Joke sunau ya documents explore karen?",
            "Acha! ✨ Kuch mazedaar pucho, ya main joke sunau? 😄",
            "Boring lag raha? 😅 Mai joke sunau? Ya kuch aur baat karen?",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # CASUAL CHAT
    # ═══════════════════════════════════════════════════════
    
    WHAT_DOING_RESPONSE = {
        'english': [
            "I'm here, ready to help you! 😊 Just waiting for your questions! What can I do for you?",
            "Just hanging out, ready to assist! ✨ What would you like to chat about?",
        ],
        'hindi': [
            "बस आपकी मदद के लिए तैयार हूं! 😊 बताइए क्या चाहिए?",
            "आपके सवालों का इंतज़ार कर रहा हूं! ✨",
        ],
        'hinglish': [
            "Bas aapki help ke liye ready hun! 😊 Batao kya karna hai?",
            "Kuch khaas nahi yaar! ✨ Aapke questions ka wait kar raha tha! Bolo!",
            "Free hun bhai! 😄 Bas aapse baat kar raha hun! Kya puchna hai?",
        ]
    }
    
    BUSY_RESPONSE = {
        'english': [
            "Never too busy for you! 😊 I'm always available. What can I help with?",
            "Free for you anytime! ✨ How can I assist?",
        ],
        'hindi': [
            "आपके लिए हमेशा फ्री हूं! 😊 बताइए क्या मदद चाहिए?",
            "बिल्कुल नहीं! ✨ कैसे मदद कर सकता हूं?",
        ],
        'hinglish': [
            "Aapke liye hamesha free hun bhai! 😊 Batao kya karna hai?",
            "Bilkul free yaar! ✨ Kaise help karu?",
            "Nahi bhai, aapke liye time hi time! 😄 Kya puchna hai?",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # APPROVALS / REJECTIONS
    # ═══════════════════════════════════════════════════════
    
    APPROVAL_RESPONSE = {
        'english': [
            "Great! 👍 Let me know if you need anything else!",
            "Awesome! ✨ I'm here if you have more questions!",
            "Perfect! 😊 Happy to help!",
        ],
        'hindi': [
            "बढ़िया! 👍 कुछ और चाहिए तो बताइए!",
            "बहुत अच्छा! ✨ कोई और सवाल हो तो पूछिए!",
        ],
        'hinglish': [
            "Mast! 👍 Aur kuch chahiye to batao!",
            "Badhiya bhai! ✨ Koi aur sawal ho to pucho!",
            "Perfect yaar! 😊 Khushi hui help karke!",
        ]
    }
    
    REJECTION_RESPONSE = {
        'english': [
            "No problem! 😊 Let me know if you change your mind or need something else!",
            "Okay! ✨ I'm here if you need me later!",
        ],
        'hindi': [
            "कोई बात नहीं! 😊 जब चाहिए तब बताइए!",
            "ठीक है! ✨ कुछ और चाहिए तो पूछिए!",
        ],
        'hinglish': [
            "Koi baat nahi bhai! 😊 Jab chahiye tab batao!",
            "Theek hai yaar! ✨ Kuch aur chahiye to bolo!",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # CONFUSION
    # ═══════════════════════════════════════════════════════
    
    CONFUSION_RESPONSE = {
        'english': [
            "Let me explain better! 😊 Could you tell me what specific part was confusing? Or rephrase your question?",
            "Sorry for the confusion! 🙏 Can you ask me again or be more specific?",
        ],
        'hindi': [
            "माफ कीजिए! 😊 क्या आप दोबारा specifically बता सकते हैं?",
            "Sorry! 🙏 कौन सा हिस्सा समझ नहीं आया? दोबारा पूछिए!",
        ],
        'hinglish': [
            "Sorry bhai, samjha nahi! 😊 Dubara specifically batao kya puchna hai?",
            "Maafi yaar! 🙏 Kaunsa part confusing tha? Phir se pucho clearly!",
            "Are sorry! 😅 Mujhe samjhao kya jaanna hai exactly?",
        ]
    }
    
    # ═══════════════════════════════════════════════════════
    # TIME/DATE
    # ═══════════════════════════════════════════════════════
    
    @classmethod
    def get_time_response(cls, language: str) -> str:
        now = datetime.now()
        time_str = now.strftime("%I:%M %p")
        
        if language == 'hindi':
            return f"⏰ अभी समय है: **{time_str}**"
        elif language == 'hinglish':
            return f"⏰ Abhi time hai: **{time_str}** bhai!"
        else:
            return f"⏰ Current time is: **{time_str}**"
    
    @classmethod
    def get_date_response(cls, language: str) -> str:
        now = datetime.now()
        date_str = now.strftime("%A, %d %B %Y")
        
        if language == 'hindi':
            return f"📅 आज की तारीख: **{date_str}**"
        elif language == 'hinglish':
            return f"📅 Aaj ki date hai: **{date_str}** bhai!"
        else:
            return f"📅 Today is: **{date_str}**"
    
    # ═══════════════════════════════════════════════════════
    # HELP & IDENTITY
    # ═══════════════════════════════════════════════════════
    
    HELP = {
        'english': """🤖 **How I can help you:**

📄 **Document Queries**
Ask anything about your uploaded documents
_"What is RAG?", "Summarize the document"_

🌐 **Translations**  
Translate between languages
_"Translate to Hindi: Hello"_

💬 **Friendly Chat**
Just talk to me!
_"How are you?", "Good morning"_

🕐 **Time & Date**
_"What time is it?", "Today's date"_

😄 **Fun Stuff**
_"Tell me a joke"_

**Languages Supported:**
🇬🇧 English • 🇮🇳 Hindi • 🇮🇳 Hinglish

What would you like to try?""",

        'hindi': """🤖 **मैं आपकी कैसे मदद कर सकता हूं:**

📄 **Documents के सवाल**
अपने uploaded documents के बारे में पूछें
_"RAG क्या है?", "Document summarize करो"_

🌐 **Translation**  
भाषाओं के बीच translate करें
_"Translate to Hindi: Hello"_

💬 **दोस्ताना बातचीत**
बस मुझसे बात करें!
_"कैसे हो?", "नमस्ते"_

🕐 **समय और तारीख**
_"क्या समय है?", "आज की तारीख"_

😄 **मज़ेदार बातें**
_"एक चुटकुला सुनाओ"_

**Supported भाषाएं:**
🇬🇧 English • 🇮🇳 हिंदी • 🇮🇳 Hinglish

क्या try करना चाहेंगे?""",

        'hinglish': """🤖 **Main aapki kaise help kar sakta hun:**

📄 **Document Questions**
Apne uploaded documents ke baare mein pucho
_"What is RAG?", "Document summarize karo"_

🌐 **Translations**  
Languages translate karo
_"Translate to Hindi: Hello"_

💬 **Friendly Baat-cheet**
Bas mujhse baat karo!
_"Kaise ho?", "Good morning"_

🕐 **Time & Date**
_"Time kya hai?", "Aaj ki date"_

😄 **Fun Stuff**
_"Joke sunao"_

**Languages Supported:**
🇬🇧 English • 🇮🇳 Hindi • 🇮🇳 Hinglish

Kya try karna hai bhai?"""
    }
    
    IDENTITY = {
        'english': """🤖 **About Me:**

I'm **RAG Assistant** - your AI-powered chat buddy!

**What I do:**
✨ Answer questions from your documents
🌐 Speak multiple languages (English, Hindi, Hinglish)
📄 Process PDFs, Excel, images, and more
💬 Have friendly conversations
🚀 Provide accurate, source-cited answers

**Powered by:**
• 🧠 Llama 3.2 AI
• 🔍 BGE-M3 embeddings
• 💾 PostgreSQL database

What would you like to know?""",

        'hindi': """🤖 **मेरे बारे में:**

मैं हूं **RAG Assistant** - आपका AI-powered chat दोस्त!

**मैं क्या करता हूं:**
✨ आपके documents से जवाब देता हूं
🌐 कई भाषाएं बोलता हूं (English, Hindi, Hinglish)
📄 PDFs, Excel, images सब process करता हूं
💬 Friendly बातचीत करता हूं
🚀 Accurate जवाब देता हूं

क्या जानना चाहेंगे?""",

        'hinglish': """🤖 **Mere baare mein:**

Main hun **RAG Assistant** - aapka AI-powered chat dost!

**Main kya karta hun:**
✨ Aapke documents se questions ke answers deta hun
🌐 Multiple languages bolta hun (English, Hindi, Hinglish)
📄 PDFs, Excel, images sab process karta hun
💬 Friendly baat-cheet karta hun
🚀 Accurate answers deta hun

**Powered by:**
• 🧠 Llama 3.2 AI
• 🔍 BGE-M3 embeddings
• 💾 PostgreSQL database

Kya jaanna hai bhai?"""
    }
    
    NO_DOCUMENTS = {
        'english': "I don't see any uploaded documents yet. Please upload a document first, and I'll help answer questions about it!\n\n📤 Supported: PDF, DOCX, Excel, CSV, TXT, Images",
        
        'hindi': "मुझे कोई uploaded documents नहीं दिख रहे। पहले एक document upload करें!\n\n📤 Supported: PDF, DOCX, Excel, CSV, TXT, Images",
        
        'hinglish': "Abhi koi documents nahi dikh rahe bhai. Pehle ek document upload karo!\n\n📤 Supported: PDF, DOCX, Excel, CSV, TXT, Images"
    }
    
    # ═══════════════════════════════════════════════════════
    # METHODS
    # ═══════════════════════════════════════════════════════
    
    @classmethod
    def get_response(cls, intent: str, language: str = 'english') -> str:
        """Get response based on intent and language"""
        
        intent_map = {
            'greeting': cls.GREETINGS,
            'morning_greeting': cls.MORNING,
            'afternoon_greeting': cls.AFTERNOON,
            'evening_greeting': cls.EVENING,
            'night_greeting': cls.NIGHT,
            'how_are_you': cls.HOW_ARE_YOU,
            'farewell': cls.FAREWELLS,
            'thanks': cls.THANKS,
            'compliment': cls.COMPLIMENTS_RESPONSE,
            'complaint': cls.COMPLAINTS_RESPONSE,
            'sad_emotion': cls.SAD_RESPONSE,
            'happy_emotion': cls.HAPPY_RESPONSE,
            'tired_emotion': cls.TIRED_RESPONSE,
            'bored_emotion': cls.BORED_RESPONSE,
            'what_doing': cls.WHAT_DOING_RESPONSE,
            'busy_question': cls.BUSY_RESPONSE,
            'approval': cls.APPROVAL_RESPONSE,
            'rejection': cls.REJECTION_RESPONSE,
            'confusion': cls.CONFUSION_RESPONSE,
        }
        
        # Handle time/date specially
        if intent == 'time_question':
            return cls.get_time_response(language)
        
        if intent == 'date_question':
            return cls.get_date_response(language)
        
        # Handle help/identity
        if intent == 'help':
            return cls.HELP.get(language, cls.HELP['english'])
        
        if intent == 'identity':
            return cls.IDENTITY.get(language, cls.IDENTITY['english'])
        
        # Random response from templates
        templates_dict = intent_map.get(intent)
        if not templates_dict:
            return cls.GREETINGS['english'][0]  # Fallback
        
        templates = templates_dict.get(language, templates_dict.get('english', []))
        return random.choice(templates) if templates else "Hello! How can I help you?"
    
    # Legacy methods
    @classmethod
    def get_greeting(cls, language: str = 'english') -> str:
        return cls.get_response('greeting', language)
    
    @classmethod
    def get_farewell(cls, language: str = 'english') -> str:
        return cls.get_response('farewell', language)
    
    @classmethod
    def get_thanks(cls, language: str = 'english') -> str:
        return cls.get_response('thanks', language)
    
    @classmethod
    def get_help(cls, language: str = 'english') -> str:
        return cls.get_response('help', language)
    
    @classmethod
    def get_identity(cls, language: str = 'english') -> str:
        return cls.get_response('identity', language)
    
    @classmethod
    def get_no_documents(cls, language: str = 'english') -> str:
        return cls.NO_DOCUMENTS.get(language, cls.NO_DOCUMENTS['english'])


# Global instance
templates = ResponseTemplates()
