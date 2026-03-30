import os, logging, asyncio
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    BotCommand,
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)
from telegram.error import TelegramError
from poetry_content import POETS

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("khayyal")

TOKEN = os.environ.get("KHAYYAL_BOT_TOKEN", "")

# ═══════════════════════════════════════════════════════
#  رسائل ثابتة
# ═══════════════════════════════════════════════════════

WELCOME = (
    "🌙 *أهلاً بك في بوت خَيال*\n\n"
    "هنا تجد قصائد كبار الشعراء كاملةً\n"
    "اختر شاعراً .. وتذوّق الكلمة 🖊️"
)

SEP = "─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─"

# ═══════════════════════════════════════════════════════
#  لوحة المفاتيح — قائمة الشعراء
# ═══════════════════════════════════════════════════════

def poets_keyboard():
    rows = []
    keys = list(POETS.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(
            f"{POETS[keys[i]]['label']}  {POETS[keys[i]]['name']}",
            callback_data=f"poet_{keys[i]}",
        )]
        if i + 1 < len(keys):
            k2 = keys[i + 1]
            row.append(InlineKeyboardButton(
                f"{POETS[k2]['label']}  {POETS[k2]['name']}",
                callback_data=f"poet_{k2}",
            ))
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def poems_keyboard(poet_key):
    poet = POETS[poet_key]
    rows = []
    for pk in poet["poems"]:
        rows.append([InlineKeyboardButton(
            f"📜  {poet['poems'][pk]['title']}",
            callback_data=f"poem:{poet_key}:{pk}",
        )])
    rows.append([InlineKeyboardButton("🔙 رجوع للشعراء", callback_data="back_poets")])
    return InlineKeyboardMarkup(rows)

def back_to_poet_keyboard(poet_key):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع لقصائده", callback_data=f"poet_{poet_key}")],
        [InlineKeyboardButton("🔙 قائمة الشعراء", callback_data="back_poets")],
    ])

# ═══════════════════════════════════════════════════════
#  الأوامر
# ═══════════════════════════════════════════════════════

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME,
        parse_mode="Markdown",
        reply_markup=poets_keyboard(),
    )

async def cmd_poets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *اختر شاعراً:*",
        parse_mode="Markdown",
        reply_markup=poets_keyboard(),
    )

# ═══════════════════════════════════════════════════════
#  معالج الأزرار
# ═══════════════════════════════════════════════════════

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_poets":
        await query.message.reply_text(
            "📖 *اختر شاعراً:*",
            parse_mode="Markdown",
            reply_markup=poets_keyboard(),
        )
        return

    if data.startswith("poet_"):
        poet_key = data[5:]
        if poet_key not in POETS:
            return
        poet = POETS[poet_key]
        text = (
            f"{poet['label']}\n"
            f"*{poet['name']}*\n\n"
            f"اختر قصيدة:"
        )
        await query.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=poems_keyboard(poet_key),
        )
        return

    if data.startswith("poem:"):
        parts = data[5:].split(":", 1)
        if len(parts) < 2:
            return
        poet_key = parts[0]
        poem_key = parts[1]

        if poet_key not in POETS or poem_key not in POETS[poet_key]["poems"]:
            return

        poem = POETS[poet_key]["poems"][poem_key]
        poet = POETS[poet_key]
        text = (
            f"📜 *{poem['title']}*\n"
            f"✍️ _{poet['name']}_\n\n"
            f"{SEP}\n\n"
            f"{poem['text']}\n\n"
            f"{SEP}"
        )
        await query.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=back_to_poet_keyboard(poet_key),
        )
        return

# ═══════════════════════════════════════════════════════
#  معالج الرسائل النصية
# ═══════════════════════════════════════════════════════

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    if msg in ("خيال", "خَيال", "قائمة", "القائمة", "الشعراء", "start"):
        await update.message.reply_text(
            WELCOME,
            parse_mode="Markdown",
            reply_markup=poets_keyboard(),
        )

# ═══════════════════════════════════════════════════════
#  تشغيل البوت
# ═══════════════════════════════════════════════════════

async def set_commands(app):
    await app.bot.set_my_commands([
        BotCommand("start",  "الرئيسية"),
        BotCommand("poets",  "قائمة الشعراء"),
    ])

def main():
    if not TOKEN:
        logger.error("❌ KHAYYAL_BOT_TOKEN غير موجود!")
        return

    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("poets",  cmd_poets))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.post_init = set_commands

    logger.info("🌙 بوت خَيال يعمل...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
