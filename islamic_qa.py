import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

GEMINI_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_KEY:
    logger.error("GEMINI_API_KEY غير موجود!")
    genai.configure(api_key="dummy")
else:
    genai.configure(api_key=GEMINI_KEY)

SYSTEM_PROMPT = """أنت عالم دين إسلامي متخصص وودود ودقيق.
أجب على الأسئلة الدينية والسيرة والقرآن والحديث والفقه بطريقة واضحة، مباشرة، ومفيدة.
استخدم لغة عربية فصحى سهلة.
إذا أمكن اذكر المصدر باختصار (مثل: رواه البخاري، سورة البقرة آية 255...).
لا ترفض أي سؤال ديني.
كن مختصراً قدر الإمكان ومفيداً.
استخدم 🤍 فقط في نهاية الرد."""

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
        prompt = f"السؤال: {question}\n\nأجب بطريقة واضحة ومفيدة:"

        response = model.generate_content(prompt)

        if response and response.text:
            answer = response.text.strip()
            if len(answer) > 20:          # للتأكد أن الرد مفيد
                return answer + "\n\n🤍"
        
        return "الله أعلم 🤍"

    except Exception as e:
        logger.error(f"خطأ في Gemini: {str(e)}")
        return "حدث خطأ فني بسيط، حاول مرة أخرى 🤍"
