import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

GEMINI_KEY = "AIzaSyCKN106cSz4SsFVJZHfLswYJWLKYwFEgbw"
genai.configure(api_key=GEMINI_KEY)

async def ask_islamic_question(question, user_id=None):
    try:
        # استخدام الموديل البسيط والسريع
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "أنت عالم دين إسلامي. أجب باختصار ومصادر موثوقة 🤍. "
            "بدون تشكيل ولا إيموجي ملونة.\n\n"
            f"السؤال: {question}"
        )
        
        # تشغيل الطلب بشكل صحيح ومباشر
        response = await model.generate_content_async(prompt)
        
        if response and response.text:
            return response.text
        return "الله أعلم، لم أجد إجابة حالياً 🤍"
        
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "الله أعلم، حاول مرة أخرى لاحقاً 🤍"

def clear_history(user_id):
    pass
