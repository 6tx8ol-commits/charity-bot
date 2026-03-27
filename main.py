import telebot
from telebot import types
from datetime import datetime
import pytz
import http.server
import socketserver
import threading

# --- سيرفر وهمي لتشغيل البوت مجاناً على Render ---
def run_dummy_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", 8080), handler) as httpd:
        httpd.serve_forever()

# --- إعدادات البوت ---
TOKEN = '8691783072:AAE5cVJOPL6LWqk6Bp_qEDJw1JYLlxTXSGw'
bot = telebot.TeleBot(TOKEN)

def get_sep():
    now = datetime.now(pytz.timezone('Asia/Riyadh'))
    return f"\n\n— — — — — — — — — —\n📅 {now.strftime('%d-%m-%Y')} | ⏰ {now.strftime('%I:%M %p')}\n— — — — — — — — — —"

def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📖 القرآن الكريم", callback_data="quran"),
        types.InlineKeyboardButton("📜 سير الصحابة", callback_data="sahaba")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "مرحباً بك 🤍\nاختر من القائمة:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    cid, mid = call.message.chat.id, call.message.message_id
    
    if call.data == "back_main":
        bot.edit_message_text("القائمة الرئيسية:", cid, mid, reply_markup=main_menu())
    elif call.data == "quran":
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("سورة الكهف (رابط خارجي)", url="https://t.me/Quran_pages_bot"),
            types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")
        )
        bot.edit_message_text("📖 القرآن الكريم - صفحات مزدوجة:", cid, mid, reply_markup=markup)
    elif call.data == "sahaba":
        markup = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("عثمان بن عفان رضي الله عنه", callback_data="othman"),
            types.InlineKeyboardButton("⬅️ رجوع", callback_data="back_main")
        )
        bot.edit_message_text("📜 اختر الصحابي:", cid, mid, reply_markup=markup)
    elif call.data == "othman":
        markup = types.InlineKeyboardMarkup(row_width=1).add(
            types.InlineKeyboardButton("📖 مسيرته", callback_data="oth_bio"),
            types.InlineKeyboardButton("💍 زوجاته", callback_data="oth_wives"),
            types.InlineKeyboardButton("👨‍👩‍👧‍👦 أبناؤه", callback_data="oth_kids"),
            types.InlineKeyboardButton("⬅️ رجوع", callback_data="sahaba")
        )
        bot.edit_message_text("⭐ عثمان بن عفان رضي الله عنه\nاختر القسم:", cid, mid, reply_markup=markup)
    elif call.data == "oth_bio":
        bot.edit_message_text("عثمان بن عفان: ثالث الخلفاء الراشدين، لُقب بذي النورين وجهز جيش العسرة." + get_sep(), cid, mid, 
                             reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="othman")))
    elif call.data == "oth_wives":
        bot.edit_message_text("زوجاته: رقية بنت رسول الله ﷺ، ثم أم كلثوم، ثم نائلة بنت الفرافصة." + get_sep(), cid, mid, 
                             reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="othman")))
    elif call.data == "oth_kids":
        bot.edit_message_text("أبناؤه: عبدالله، عمرو، خالد، أبان، عمر، مريم، وأم سعيد رضي الله عنهم." + get_sep(), cid, mid, 
                             reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ رجوع", callback_data="othman")))

if __name__ == "__main__":
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
