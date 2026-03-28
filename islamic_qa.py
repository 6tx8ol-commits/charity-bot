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
        import requests
        url = "https://api.affiliateplus.xyz/api/chatbot"
        params = {
            "message": question,
            "ownername": "Turki",
            "botname": "IslamBot"
        }
        response = requests.get(url, params=params, timeout=8)
        data = response.json()
        if data.get("message"):
            return data.get("message")
    except:
        pass

    return "سؤال جميل 🤍
لكن حالياً ما عندي جواب دقيق.
جرب تعيد صياغة السؤال بشكل أوضح."
