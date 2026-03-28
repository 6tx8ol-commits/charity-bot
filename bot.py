import os
import logging
import datetime
from zoneinfo import ZoneInfo
import pytz
from hijridate import Gregorian
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# استيراد المحتوى
from content import (
    MORNING_AZKAR_TEXT, EVENING_AZKAR_TEXT, SLEEP_AZKAR_TEXT,
    SALAWAT_TEXT, ISTIJABA_TEXT, SOCIAL_TEXT, KAHF_TEXT,
    WELCOME_TEXT, HELP_TEXT,
    get_random_azkar_sabah, get_random_azkar_masa, get_random_azkar_nawm,
    get_prayer_times_text, get_prayer_times_for_location,
    get_single_prayer_text, PRAYER_NAMES_ORDER, SAUDI_REGIONS, SAUDI_CITIES
)
from islamic_qa import ask_islamic_question

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN غير موجود!")

# معالجة CHANNEL_ID
_raw = os.environ.get("TELEGRAM_CHANNEL_ID", "").strip()
if _raw.startswith(("https://t.me/", "t.me/")):
    CHANNEL_ID = "@" + _raw.split("t.me/")[-1].strip("/")
else:
    CHANNEL_ID = _raw

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
TIMEZONE = ZoneInfo("Asia/Riyadh")
PYTZ_TZ = pytz.timezone("Asia/Riyadh")

# ====================== التاريخ ======================
HIJRI_MONTHS = {1:"محرم",2:"صفر",3:"ربيع الأول",4:"ربيع الثاني",5:"جمادى الأولى",6:"جمادى الثانية",
                7:"رجب",8:"شعبان",9:"رمضان",10:"شوال",11:"ذو القعدة",12:"ذو الحجة"}

GREGORIAN_MONTHS = {1:"يناير",2:"فبراير",3:"مارس",4:"أبريل",5:"مايو",6:"يونيو",7:"يوليو",
                     8:"أغسطس",9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"}

DAYS_AR = {0:"الاثنين",1:"الثلاثاء",2:"الأربعاء",3:"الخميس",4:"الجمعة",5:"السبت",6:"الأحد"}

def get_date_line():
    now = datetime.datetime.now(TIMEZONE)
    hijri = Gregorian(now.year, now.month, now.day).to_hijri()
    day_name = DAYS_AR.get(now.weekday(), "")
    h_text = f"{hijri.day} {HIJRI_MONTHS.get(hijri.month, '')} {hijri.year} هـ"
    g_text = f"{now.day} {GREGORIAN_MONTHS.get(now.month, '')} {now.year} م"
    time_text = now.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    return f"• {day_name} — {time_text} •\n• {h_text} — {g_text} •"

# ====================== إرسال إلى القناة ======================
async def send_to_channel(bot: Bot, text: str, image: str = None):
    full_text = f"{text}\n\n{get_date_line()}"
    try:
        if image:
            path = os.path.join(IMAGES_DIR, image)
            if os.path.exists(path):
                with open(path, "rb") as f:
                    await bot.send_photo(chat_id=CHANNEL_ID, photo=f, caption=full_text)
                return
        await bot.send_message(chat_id=CHANNEL_ID, text=full_text, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"فشل إرسال للقناة: {e}")

# ====================== المهام المجدولة ======================
async def job_morning(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, MORNING_AZKAR_TEXT, "morning.jpg")

async def job_evening(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, EVENING_AZKAR_TEXT, "evening.jpg")

async def job_sleep(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, SLEEP_AZKAR_TEXT, "sleep.jpg")

async def job_kahf(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, KAHF_TEXT)

async def job_salawat(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, SALAWAT_TEXT)

async def job_istijaba(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, ISTIJABA_TEXT)

async def job_social(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, SOCIAL_TEXT)

# ====================== الكيبوردات ======================
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("أذكار الصباح", callback_data="sabah")],
        [InlineKeyboardButton("أذكار المساء", callback_data="masa")],
        [InlineKeyboardButton("أذكار النوم", callback_data="nawm")],
        [InlineKeyboardButton("أوقات الصلاة", callback_data="prayer_times")],
        [InlineKeyboardButton("قناة أثر", url="https://t.me/Athar_Atkar")],
    ])

def back_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("رجوع للقائمة", callback_data="menu")]])

# ====================== Handlers ======================
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, reply_markup=main_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu":
        await query.message.reply_text(HELP_TEXT, reply_markup=main_keyboard())
        return

    if data == "sabah":
        text = get_random_azkar_sabah()
    elif data == "masa":
        text = get_random_azkar_masa()
    elif data == "nawm":
        text = get_random_azkar_nawm()
    elif data == "prayer_times":
        text = get_prayer_times_text()
        await query.message.reply_text(text, reply_markup=back_keyboard())
        return
    else:
        text = HELP_TEXT

    await query.message.reply_text(text)
    await query.message.reply_text(get_date_line())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    msg = update.message.text.strip()

    # أوقات الصلاة
    if msg in ("اوقات الصلاة", "أوقات الصلاة", "الصلاة", "مواقيت الصلاة"):
        await update.message.reply_text(get_prayer_times_text(), reply_markup=back_keyboard())
        return

    # أوامر القائمة
    if msg in ("اثر", "أثر", "القائمة", "المساعدة", "help", "/athar"):
        await update.message.reply_text(HELP_TEXT, reply_markup=main_keyboard())
        return

    # الأسئلة الدينية عبر Gemini (الجزء المعدل)
    if len(msg) > 3:
        answer = ask_islamic_question(msg)
        await update.message.reply_text(answer)
        await update.message.reply_text(get_date_line())   # التاريخ مرة واحدة فقط

# ====================== تشغيل البوت ======================
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Job Queue
    jq = application.job_queue

    jq.run_daily(job_morning,  time=datetime.time(5, 15, tzinfo=PYTZ_TZ))
    jq.run_daily(job_evening,  time=datetime.time(18, 30, tzinfo=PYTZ_TZ))
    jq.run_daily(job_sleep,    time=datetime.time(21, 30, tzinfo=PYTZ_TZ))

    # يوم الجمعة
    jq.run_daily(job_kahf,     time=datetime.time(8, 30, tzinfo=PYTZ_TZ), days=(5,))
    jq.run_daily(job_salawat,  time=datetime.time(8, 30, tzinfo=PYTZ_TZ), days=(5,))
    jq.run_daily(job_istijaba, time=datetime.time(16, 30, tzinfo=PYTZ_TZ), days=(5,))
    jq.run_daily(job_social,   time=datetime.time(20, 0,  tzinfo=PYTZ_TZ), days=(5,))

    logger.info("✅ البوت جاهز")
    print("🚀 البوت بدأ العمل الآن...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
