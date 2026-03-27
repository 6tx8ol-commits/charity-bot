import telebot
from telebot import types
from datetime import datetime
import pytz

TOKEN = '8691783072:AAE5cVJOPL6LWqk6Bp_qEDJw1JYLlxTXSGw'
bot = telebot.TeleBot(TOKEN)

# دالة الفاصل الزمني
def get_sep():
    try:
        now = datetime.now(pytz.timezone('Asia/Riyadh'))
        return f"\n\n— — — — — — — — — —\n📅 {now.strftime('%d-%m-%Y')} | ⏰ {now.strftime('%I:%M %p')}\n— — — — — — — — — —"
    except: return ""

# --- القائمة الرئيسية ---
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📖 القرآن الكريم", callback_data="go_quran"),
        types.InlineKeyboardButton("🕌 أوقات الصلاة", callback_data="go_regions"),
        types.InlineKeyboardButton("📜 سير الصحابة", callback_data="go_sahaba"),
        types.InlineKeyboardButton("✨ الأذكار اليومية", callback_data="go_athkar")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "أهلاً بك في بوت صدقة جارية عن غازي عجاج 🤍\nاختر من القائمة أدناه:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    cid = call.message.chat.id
    mid = call.message.message_id
    data = call.data

    # --- الرجوع للقائمة الرئيسية ---
    if data == "main_menu":
        bot.edit_message_text("اختر من القائمة أدناه:", cid, mid, reply_markup=main_menu())

    # --- قسم الصحابة ---
    elif data == "go_sahaba":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("عثمان بن عفان", callback_data="sahabi_othman"),
                   types.InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
        bot.edit_message_text("📜 اختر الصحابي:", cid, mid, reply_markup=markup)

    elif data == "sahabi_othman":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("📖 سيرته", callback_data="othman_bio"),
            types.InlineKeyboardButton("💍 زوجاته", callback_data="othman_wives"),
            types.InlineKeyboardButton("👨‍👩‍👧‍👦 أبناؤه", callback_data="othman_kids"),
            types.InlineKeyboardButton("⬅️ رجوع", callback_data="go_sahaba")
        )
        bot.edit_message_text("⭐ عثمان بن عفان رضي الله عنه\nاختر القسم الذي تريد القراءة عنه:", cid, mid, reply_markup=markup)

    elif data == "othman_bio":
        text = "عثمان بن عفان الأموي القرشي، ثالث الخلفاء الراشدين وأحد العشرة المبشرين بالجنة، لُقب بذي النورين."
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="sahabi_othman"))
        bot.edit_message_text(text + get_sep(), cid, mid, reply_markup=markup)

    elif data == "othman_wives":
        text = "من زوجاته: رقية بنت رسول الله ﷺ، أم كلثوم بنت رسول الله ﷺ، فاختة بنت غزوان، ونائلة بنت الفرافصة."
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="sahabi_othman"))
        bot.edit_message_text(text + get_sep(), cid, mid, reply_markup=markup)

    elif data == "othman_kids":
        text = "أبناؤه: عبدالله (من رقية)، عمرو، خالد، أبان، عمر، مريم، وأم سعيد."
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="sahabi_othman"))
        bot.edit_message_text(text + get_sep(), cid, mid, reply_markup=markup)

    # --- قسم القرآن (رابط خارجي) ---
    elif data == "go_quran":
        markup = types.InlineKeyboardMarkup(row_width=1)
        # الرابط المباشر الذي طلبته لصفحة الكهف المزدوجة
        markup.add(types.InlineKeyboardButton("سورة الكهف (صفحة مزدوجة)", url="https://pcloud.com/publink/show?code=XZ7k0VXZ7k0VXZ7k0V"),
                   types.InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
        bot.edit_message_text("📖 اختر السورة لفتح الرابط المباشر:", cid, mid, reply_markup=markup)

    # --- قسم مناطق السعودية (شامل) ---
    elif data == "go_regions":
        markup = types.InlineKeyboardMarkup(row_width=2)
        regions = ["الوسطى (الرياض)", "الغربية (مكة/جدة)", "الشرقية", "الشمالية", "الجنوبية"]
        buttons = [types.InlineKeyboardButton(r, callback_data=f"reg_{r}") for r in regions]
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
        bot.edit_message_text("🕌 اختر المنطقة لمعرفة أوقات الصلاة:", cid, mid, reply_markup=markup)

    elif data.startswith("reg_"):
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="go_regions"))
        bot.edit_message_text(f"سيتم عرض أوقات الصلاة لمنطقة {data.split('_')[1]} فور توفر التحديث." + get_sep(), cid, mid, reply_markup=markup)

bot.polling(none_stop=True)
