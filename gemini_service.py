import os
import google.generativeai as genai
import logging

logger = logging.getLogger("GeminiService")

# الحصول على المفتاح من البيئة
GEMINI_KEY = os.getenv("GEMINI_API_KEY", None)

if not GEMINI_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in the environment variables.")

# Configure the API key
genai.configure(api_key=GEMINI_KEY)

# إعداد النموذج
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config={
        "temperature": 0.7,
        "top_p": 0.95,
        "max_output_tokens": 1000,
    }
)

# استدعاء الجواب
def ask_gemini(question):
    try:
        response = model.generate_content(question)
        return response.text
    except Exception as e:
        logger.error(f"Error while generating content: {str(e)}")
        return "عذراً، حدث خطأ أثناء إنشاء الإجابة."