import os
import logging
import time
from openai import OpenAI

logger = logging.getLogger(__name__)

client = None
conversation_history = {}
MAX_HISTORY = 10
HISTORY_TIMEOUT = 1800

def _get_client():
    global client
    if client is None:
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
        if base_url and api_key:
            client = OpenAI(base_url=base_url, api_key=api_key)
        else:
            client = OpenAI()
    return client

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
- اذا ارسل المستخدم معلومة دينية خاطئة وانت متاكد انها خاطئة فصححها بادب ولطف مع ذكر الدليل من القرآن او السنة
- اذا ارسل معلومة صحيحة امدحه وشجعه وزده علما
- اذا كانت المعلومة فيها خلاف بين العلماء وضح ذلك ولا تجزم
- تذكر سياق المحادثة السابقة مع المستخدم وارجع لها عند الحاجة
- كن كأنك تتحاور مع صديق تحبه وتريد له الخير
- اذا لم تكن متاكدا من معلومة لا تجزم بها وقل: الله اعلم، وانصح بالرجوع لاهل العلم"""


def _get_history(user_id):
    now = time.time()
    if user_id in conversation_history:
        data = conversation_history[user_id]
        if now - data["last_time"] > HISTORY_TIMEOUT:
            conversation_history[user_id] = {"messages": [], "last_time": now}
        else:
            data["last_time"] = now
    else:
        conversation_history[user_id] = {"messages": [], "last_time": now}
    return conversation_history[user_id]["messages"]


def _trim_history(messages):
    if len(messages) > MAX_HISTORY * 2:
        return messages[-(MAX_HISTORY * 2):]
    return messages


def clear_history(user_id):
    if user_id in conversation_history:
        del conversation_history[user_id]


def ask_islamic_question(question, user_id=None):
    try:
        c = _get_client()

        if user_id:
            history = _get_history(user_id)
            history.append({"role": "user", "content": question})
            history = _trim_history(history)
            conversation_history[user_id]["messages"] = history

            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history
        else:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ]

        response = c.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=1000,
            temperature=0.3,
        )
        answer = response.choices[0].message.content

        if user_id:
            history.append({"role": "assistant", "content": answer})
            conversation_history[user_id]["messages"] = _trim_history(history)

        return answer
    except Exception as e:
        logger.error(f"AI Q&A error: {e}")
        return None
