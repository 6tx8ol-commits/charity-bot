import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

GEMINI_KEY = "AIzaSyCKN106cSz4SsFVJZHfLswYJWLKYwFEgbw"
genai.configure(api_key=GEMINI_KEY)

async def ask_islamic_question(question):
    try:
        # تأكدنا من اسم الموديل الصحيح هنا
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = (
            "أنت عالم دين إسلامي متخصص. أجب فقط على الأسئلة الدينية 🤍. "
            "بدون تشكيل، بدون إيموجي ملون، باختصار مفيد مع ذكر المصادر.\n\n"
            f"السؤال: {question}"
        )

        response = model.generate_content(prompt)
        # أضفنا التحقق من وجود نص في الرد
        if response and response.text:
            return response.text
        else:
            return "الله اعلم، لم أجد إجابة دقيقة حالياً 🤍"
            
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        # غيرنا الرسالة هنا عشان نعرف لو لسه فيه خطأ
        return f"الله اعلم، (Error: {str(e)[:20]}) 🤍"
