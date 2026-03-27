import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

# إعداد Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

# ذاكرة المحادثات
chat_sessions = {}

SYSTEM_PROMPT = """انت عالم دين اسلامي متخصص ومحاور ودود. تتحاور مع المستخدم وتجيب على اسئلته الدينية.

القواعد:
- اجب فقط على الاسئلة المتعلقة بالاسلام والقرآن والسنة والانبياء والصحابة والفقه والعقيدة
- استند في اجاباتك على القرآن الكريم والسنة النبوية الصحيحة واقوال العلماء المعتبرين
- لا تستخدم الحركات (التشكيل) في النص العربي
- لا تستخدم ايموجي ملونة — فقط 🤍
- اذا كان السؤال غير ديني قل: هذا البوت مخصص للمحتوى الديني فقط 🤍
- اجب بشكل مختصر ومفيد ولا تطيل كثيرا
- اذكر المصدر اذا كان من القرآن او الحديث
- لا تفتي في مسائل خلافية معقدة بل انصح بسؤال اهل العلم

قواعد النقاش والتصحيح:
- اذا ارسل المستخدم معلومة دينية خاطئة فصححها بادب ولطف مع ذكر الدليل
- اذا ارسل معلومة صحيحة امدحه وشجعه وزده علما
- تذكر سياق المحادثة السابقة مع المستخدم وارجع لها عند الحاجة
- كن كأنك تتحاور مع صديق تحبه وتريد له الخير
- اذا لم تكن متاكدا قل: الله اعلم"""

def ask_islamic_question(question, user_id=None):
    try:
        # إذا المستخدم ماله جلسة، نفتح له وحدة جديدة مع القواعد
        if user_id not in chat_sessions:
            chat_sessions[user_id] = model.start_chat(history=[])
            # أول رسالة "توجيهية" للبوت
            chat_sessions[user_id].send_message(SYSTEM_PROMPT)

        # إرسال السؤال واستلام الرد
        response = chat_sessions[user_id].send_message(question)
        answer = response.text
        
        return answer
    except Exception as e:
        logger.error(f"Gemini AI error: {e}")
        return "الله اعلم، حدث خطأ فني بسيط 🤍"

def clear_history(user_id):
    if user_id in chat_sessions:
        del chat_sessions[user_id]
