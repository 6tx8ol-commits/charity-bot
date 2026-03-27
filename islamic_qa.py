import os
import logging
from google import genai

logger = logging.getLogger(__name__)

# إعداد Gemini بالمكتبة الجديدة
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


# ذاكرة المحادثات
chat_sessions = {}

SYSTEM_PROMPT = """انت عالم دين اسلامي متخصص ومحاور ودود.
القواعد:
- اجب فقط على الاسئلة الدينية 🤍
- لا تستخدم التشكيل ولا ايموجي ملونة — فقط 🤍
- اذكر المصادر وباختصار مفيد
- اذا لم تكن متاكدا قل: الله اعلم"""

def ask_islamic_question(question, user_id=None):
    try:
        # إرسال السؤال مع التعليمات
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"{SYSTEM_PROMPT}\n\nالمستخدم: {question}"
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "الله اعلم، حدث خطأ فني بسيط 🤍"

def clear_history(user_id):
    pass
