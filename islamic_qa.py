import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# حطينا مفتاحك هنا مباشرة عشان نضمن يشتغل فوراً
GEMINI_KEY = "AIzaSyCKN106cSz4SsFVJZHfLswYJWLKYwFEgbw"
genai.configure(api_key=GEMINI_KEY)

# أضفنا async هنا عشان يتوافق مع البوت
async def ask_islamic_question(question, user_id=None):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # ترتيب البرومبت عشان ما يتلخبط الذكاء
        prompt = (
            "أنت عالم دين إسلامي متخصص ومحاور ودود. "
            "القواعد: أجب فقط على الأسئلة الدينية. لا تستخدم التشكيل ولا إيموجي ملونة - فقط 🤍. "
            "اذكر المصادر وباختصار مفيد. إذا لم تكن متأكداً قل: الله أعلم.\n\n"
            f"السؤال: {question}"
        )

        # نستخدم await هنا
       response = await model.generate_content_async(prompt)

        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "الله اعلم، الفكره ستطبق قريبا 🤍"

def clear_history(user_id):
    pass
