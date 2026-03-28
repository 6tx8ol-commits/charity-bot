import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# تهيئة Gemini
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_KEY:
    logger.error("GEMINI_API_KEY غير موجود!")
    genai.configure(api_key="dummy")  # لتجنب الكراش
else:
    genai.configure(api_key=GEMINI_KEY)

SYSTEM_PROMPT = """أنت عالم دين إسلامي متخصص، ودود، ودقيق.
- أجب على كل الأسئلة الدينية والسيرة والفقه والحديث والقرآن بطريقة واضحة ومفيدة.
- استخدم لغة عربية فصحى سهلة.
- اذكر المصدر باختصار إذا أمكن (مثل: من صحيح البخاري، أو من تفسير الطبري...).
- لا ترفض أي سؤال ديني إلا إذا كان واضحًا أنه غير ديني.
- استخدم إيموجي 🤍 فقط في نهاية الرد إذا أردت.
- كن مختصرًا ومفيدًا قدر الإمكان."""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT,
    generation_config={
        "temperature": 0.7,
        "max_output_tokens": 1200,
    }
)

def ask_islamic_question(question: str, user_id=None):
    try:
        response = model.generate_content(question)
        
        if response and response.text:
            text = response.text.strip()
            # إزالة أي "الله أعلم" تلقائي إذا كان الرد طويل
            if len(text) > 30 and "الله أعلم" in text and "حدث خطأ" not in text:
                return text
            return text + "\n\n🤍"
        
        return "الله أعلم 🤍"

    except Exception as e:
        logger.error(f"خطأ في Gemini: {e}")
        return "حدث خطأ فني بسيط، حاول مرة أخرى 🤍"
