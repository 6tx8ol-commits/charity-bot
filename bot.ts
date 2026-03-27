import telebot
from telebot import types
from datetime import datetime
import pytz

# ضع التوكن الخاص ببوتك هنا
TOKEN = 'YOUR_BOT_TOKEN_HERE'
bot = telebot.TeleBot(TOKEN)

# رابط مصحف الصفحات الذي أرسلته
QURAN_URL = "رابط_القرآن_الذي_أرسلته" 

# دالة لجلب الوقت والتاريخ (ميلادي) وتنسيق الفاصل
def get_separator():
    now = datetime.now(pytz.timezone('Asia/Riyadh'))
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%I:%M %p")
    day_str = now.strftime("%A")
    # يمكنك إضافة تحويل للهجري هنا إذا توفرت المكتبة، حالياً التنسيق كما طلبت:
    return f"\n\n— — — — — — — — — —\n📅 {day_str} | {date_str}\n⏰ {time_str}\n— — — — — — — — — —"

# رسالة الترحيب عند البداية
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

# التعامل مع الضغط على الأزرار
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
        # هنا يتم وضع رابط الملف الصوتي الذي رفعته على جيت هب
        # bot.send_audio(cid, 'رابط_ملف_الصوت_هنا')

    elif text == '🛑 إيقاف الصوتية':
        bot.send_message(cid, "تم إيقاف التشغيل." + get_separator())

    elif text == '📜 سير الصحابة':
        bot.send_message(cid, "قائمة الصحابة رضوان الله عليهم (يتم جلب السير الآن...): \n1. أبو بكر الصديق\n2. عمر بن الخطاب\n3. عثمان بن عفان\n4. علي بن أبي طالب" + get_separator())

    elif text == '✨ أذكار وأدعية':
        bot.send_message(cid, "أذكار الصباح والمساء وأدعية مختارة... (محتوى الأذكار)" + get_separator())

# التعامل مع القوائم المتفرعة (أوقات الصلاة)
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
                   types.InlineKeyboardButton("الخرج", callback_data="city_kharj"))
        bot.edit_message_text("اختر المدينة:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("city_"):
        markup = types.InlineKeyboardMarkup()
        btn_notif = types.InlineKeyboardButton("🔔 نبهني عند الأذان", callback_data="set_notif")
        markup.add(btn_notif)
        bot.send_message(call.message.chat.id, "أوقات الصلاة لمدينتك هي: ... \n(سيتم التحديث تلقائياً)", reply_markup=markup)

    elif call.data == "set_notif":
        bot.answer_callback_query(call.id, "تم تفعيل تنبيهات الأذان بنجاح! ✅")

bot.polling(none_stop=True)
