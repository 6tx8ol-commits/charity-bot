import telebot
from telebot import types
from datetime import datetime
import pytz

TOKEN = '8691783072:AAE5cVJOPL6LWqk6Bp_qEDJw1JYLlxTXSGw'
bot = telebot.TeleBot(TOKEN)

QURAN_URL = "https://t.me/Quran_pages_bot" 

def get_separator():
    try:
        now = datetime.now(pytz.timezone('Asia/Riyadh'))
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%I:%M %p")
        day_str = now.strftime("%A")
        days = {"Monday": "الاثنين", "Tuesday": "الثلاثاء", "Wednesday": "الأربعاء", 
                "Thursday": "الخميس", "Friday": "الجمعة", "Saturday": "السبت", "Sunday": "الأحد"}
        day_ar = days.get(day_str, day_str)
        return f"\n\n— — — — — — — — — —\n📅 {day_ar} | {date_str}\n⏰ {time_str}\n— — — — — — — — — —"
    except:
        return "\n\n— — — — — — — — — —"

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📖 القرآن الكريم')
    btn2 = types.KeyboardButton('🕌 أوقات الصلاة')
    btn3 = types.KeyboardButton('✨ أذكار وأدعية')
    btn4 = types.KeyboardButton('📜 سير الصحابة')
    btn5 = types.KeyboardButton('🔊 تكبيرات الأستاذ غازي رحمه الله')
    btn6 = types.KeyboardButton('🛑 إيقاف الصوتية')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    
    welcome_msg = (
        "أهلاً بك 🤍، هذا بوت صدقة جارية عن غازي عجاج، "
        "اللهم اغفر له وارحمه واجعلها نوراً له في قبره 🤍.\n\n"
        "اختر من الأزرار بالأسفل 👇"
    )
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    cid = message.chat.id
    text = message.text

    if text == '📖 القرآن الكريم':
        bot.send_message(cid, f"تفضل رابط صفحات القرآن الكريم: \n{QURAN_URL}" + get_separator())

    elif text == '🕌 أوقات الصلاة':
        markup = types.InlineKeyboardMarkup()
        btn_sa = types.InlineKeyboardButton("المملكة العربية السعودية 🇸🇦", callback_data="country_sa")
        markup.add(btn_sa)
        bot.send_message(cid, "اختر الدولة لمعرفة أوقات الصلاة:", reply_markup=markup)

    elif text == '🔊 تكبيرات الأستاذ غازي رحمه الله':
        bot.send_message(cid, "جاري تشغيل تكبيرات الأستاذ غازي رحمه الله... 🤍" + get_separator())

    elif text == '🛑 إيقاف الصوتية':
        bot.send_message(cid, "تم إيقاف التشغيل." + get_separator())

    elif text == '📜 سير الصحابة':
        bot.send_message(cid, "قائمة الصحابة رضوان الله عليهم:\n1. أبو بكر الصديق\n2. عمر بن الخطاب\n3. عثمان بن عفان\n4. علي بن أبي طالب\n5. الزبير بن العوام\n6. طلحة بن عبيد الله\n7. عبد الرحمن بن عوف\n8. سعد بن أبي وقاص\n9. أبو عبيدة عامر بن الجراح\n10. سعيد بن زيد" + get_separator())

    elif text == '✨ أذكار وأدعية':
        bot.send_message(cid, "أذكار الصباح والمساء وأدعية مختارة من الكتاب والسنة." + get_separator())

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == "country_sa":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("المنطقة الغربية", callback_data="reg_west"),
                   types.InlineKeyboardButton("المنطقة الشرقية", callback_data="reg_east"),
                   types.InlineKeyboardButton("منطقة الرياض", callback_data="reg_riyadh"))
        bot.edit_message_text("اختر المنطقة في السعودية:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "reg_riyadh":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("مدينة الرياض", callback_data="city_riyadh"),
                   types.InlineKeyboardButton("الخرج", callback_data="city_kharj"),
                   types.InlineKeyboardButton("المجمعة", callback_data="city_majmaah"))
        bot.edit_message_text("اختر المدينة:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "reg_west":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("مكة المكرمة", callback_data="city_makkah"),
                   types.InlineKeyboardButton("جدة", callback_data="city_jeddah"),
                   types.InlineKeyboardButton("الطائف", callback_data="city_taif"))
        bot.edit_message_text("اختر المدينة:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "reg_east":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("الدمام", callback_data="city_dammam"),
                   types.InlineKeyboardButton("الخبر", callback_data="city_khobar"),
                   types.InlineKeyboardButton("الأحساء", callback_data="city_ahsa"))
        bot.edit_message_text("اختر المدينة:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("city_"):
        markup = types.InlineKeyboardMarkup()
        btn_notif = types.InlineKeyboardButton("🔔 نبهني عند الأذان", callback_data="set_notif")
        markup.add(btn_notif)
        bot.send_message(call.message.chat.id, "أوقات الصلاة لمدينتك هي: قيد التحديث... ", reply_markup=markup)

    elif call.data == "set_notif":
        bot.answer_callback_query(call.id, "تم تفعيل تنبيهات الأذان بنجاح! ✅")

bot.polling(none_stop=True)
