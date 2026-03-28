import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """عالم دين اسلامي متخصص ومحاور ودود
:القواعد
- اجب فقط على الاسئلة الدينية 🤍
- لا تستخدم التشكيل ولا ايموجي ملونة - فقط 🤍
- اذكر المصادر وباختصار مفيد
- اذا لم تكن متأكدا قل: الله اعلم"""

def ask_islamic_question(question, user_id=None):
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            system_instruction=SYSTEM_PROMPT
        )

        response = model.generate_content(question)

        return response.text if response.text else "الله اعلم 🤍"

    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "الله اعلم، حدث خطأ فني بسيط 🤍"

def clear_history(user_id):
    pass
