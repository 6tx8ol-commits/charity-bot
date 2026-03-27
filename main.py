
import telebot
from telebot import types
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread

# كود وهمي عشان يشتغل مجاني على Render Web Service
app = Flask('')
@app.route('/')
def home(): return "البوت شغال بنجاح!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- حط التوكن حقك هنا ---
TOKEN = '8691783072:AAE5cVJOPL6LWqk6Bp_qEDJw1JYLlxTXSGw'
bot = telebot.TeleBot(TOKEN)

# دالة الفاصل الزمني
def get_sep():
    try:
        now = datetime.now(pytz.timezone('Asia/Riyadh'))
        return f"\n\n— — — — — — — — — —\n📅 {now.strftime('%d-%m-%Y')} | ⏰ {now.strftime('%I:%M %p')}\n— — — — — — — — — —"
    except: return ""

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

    if data == "main_menu":
        bot.edit_message_text("اختر من القائمة أدناه:", cid, mid, reply_markup=main_menu())
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
        bot.edit_message_text("⭐ عثمان بن عفان رضي الله عنه\nاختر القسم:", cid, mid, reply_markup=markup)
    elif data == "othman_bio":
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="sahabi_othman"))
        bot.edit_message_text("ثالث الخلفاء الراشدين وذو النورين رضي الله عنه." + get_sep(), cid, mid, reply_markup=markup)
    elif data == "othman_wives":
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="sahabi_othman"))
        bot.edit_message_text("تزوج رقية وأم كلثوم بنتي رسول الله ﷺ." + get_sep(), cid, mid, reply_markup=markup)
    elif data == "othman_kids":
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="sahabi_othman"))
        bot.edit_message_text("من أبنائه عبدالله وعمرو وأبان رضي الله عنهم." + get_sep(), cid, mid, reply_markup=markup)
    elif data == "go_quran":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("سورة الكهف (صفحة مزدوجة)", url="https://pcloud.com/publink/show?code=XZ7k0VXZ7k0VXZ7k0V"),
                   types.InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
        bot.edit_message_text("📖 اختر السورة:", cid, mid, reply_markup=markup)
    elif data == "go_regions":
        markup = types.InlineKeyboardMarkup(row_width=2)
        regions = ["الرياض", "مكة/جدة", "الشرقية", "الشمالية", "الجنوبية"]
        buttons = [types.InlineKeyboardButton(r, callback_data=f"reg_{r}") for r in regions]
        markup.add(*buttons)
        markup.add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="main_menu"))
        bot.edit_message_text("🕌 اختر المنطقة:", cid, mid, reply_markup=markup)

# تشغيل الكود الوهمي ثم البوت
if __name__ == "__main__":
    keep_alive()
    bot.polling(none_stop=True)
