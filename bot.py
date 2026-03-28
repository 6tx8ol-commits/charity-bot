import requests
import os
import logging
import datetime
import unicodedata
from zoneinfo import ZoneInfo
from hijridate import Hijri, Gregorian
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ChatMemberHandler, filters, ContextTypes
from telegram.error import TelegramError
from content import (
    get_random_azkar, get_random_azkar_sabah, get_random_azkar_masa,
    get_random_azkar_nawm, get_random_dua, get_random_nabiy, get_random_ayah,
    get_random_sahabi, get_random_quran_story, get_random_dua_nabi,
    get_random_tahseen, get_random_hadith, get_random_asma,
    get_random_fadl, get_random_azkar_salah, get_random_istighfar,
    get_random_adab, get_random_quiz, get_prayer_times_text,
    get_single_prayer_text, get_prayer_times_for_location,
    fetch_prayer_times, PRAYER_NAMES_ORDER,
    SAUDI_REGIONS, SAUDI_CITIES, PROPHETS, QURAN_SURAHS, ALLAH_NAMES,
    WELCOME_TEXT, HELP_TEXT, MORNING_AZKAR_TEXT, EVENING_AZKAR_TEXT, SLEEP_AZKAR_TEXT,
    SALAWAT_TEXT, ISTIJABA_TEXT, SOCIAL_TEXT, KAHF_TEXT, AYAT_KURSI, KHAWATIM_BAQARA, BAQIYAT
)
from islamic_qa import ask_islamic_question


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

_raw_channel = os.environ.get("TELEGRAM_CHANNEL_ID", "")
if _raw_channel.startswith("https://t.me/"):
    CHANNEL_ID = "@" + _raw_channel.split("https://t.me/")[-1].strip("/")
elif _raw_channel.startswith("t.me/"):
    CHANNEL_ID = "@" + _raw_channel.split("t.me/")[-1].strip("/")
else:
    CHANNEL_ID = _raw_channel

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
TIMEZONE = ZoneInfo("Asia/Riyadh")

HIJRI_MONTHS = {
    1: "ÙØ­Ø±Ù", 2: "ØµÙØ±", 3: "Ø±Ø¨ÙØ¹ Ø§ÙØ§ÙÙ", 4: "Ø±Ø¨ÙØ¹ Ø§ÙØ«Ø§ÙÙ",
    5: "Ø¬ÙØ§Ø¯Ù Ø§ÙØ§ÙÙÙ", 6: "Ø¬ÙØ§Ø¯Ù Ø§ÙØ«Ø§ÙÙØ©", 7: "Ø±Ø¬Ø¨", 8: "Ø´Ø¹Ø¨Ø§Ù",
    9: "Ø±ÙØ¶Ø§Ù", 10: "Ø´ÙØ§Ù", 11: "Ø°Ù Ø§ÙÙØ¹Ø¯Ø©", 12: "Ø°Ù Ø§ÙØ­Ø¬Ø©"
}

GREGORIAN_MONTHS = {
    1: "ÙÙØ§ÙØ±", 2: "ÙØ¨Ø±Ø§ÙØ±", 3: "ÙØ§Ø±Ø³", 4: "Ø§Ø¨Ø±ÙÙ",
    5: "ÙØ§ÙÙ", 6: "ÙÙÙÙÙ", 7: "ÙÙÙÙÙ", 8: "Ø§ØºØ³Ø·Ø³",
    9: "Ø³Ø¨ØªÙØ¨Ø±", 10: "Ø§ÙØªÙØ¨Ø±", 11: "ÙÙÙÙØ¨Ø±", 12: "Ø¯ÙØ³ÙØ¨Ø±"
}

DAYS_AR = {
    0: "Ø§ÙØ§Ø«ÙÙÙ", 1: "Ø§ÙØ«ÙØ§Ø«Ø§Ø¡", 2: "Ø§ÙØ§Ø±Ø¨Ø¹Ø§Ø¡", 3: "Ø§ÙØ®ÙÙØ³",
    4: "Ø§ÙØ¬ÙØ¹Ø©", 5: "Ø§ÙØ³Ø¨Øª", 6: "Ø§ÙØ§Ø­Ø¯"
}

def get_date_line():
    now = datetime.datetime.now(TIMEZONE)
    hijri = Gregorian(now.year, now.month, now.day).to_hijri()
    day_name = DAYS_AR.get(now.weekday(), "")
    h_text = f"{hijri.day} {HIJRI_MONTHS[hijri.month]} {hijri.year} ÙÙ"
    g_text = f"{now.day} {GREGORIAN_MONTHS[now.month]} {now.year} Ù"
    time_text = now.strftime("%I:%M %p").replace("AM", "Øµ").replace("PM", "Ù")
    line1 = f"â¢ {day_name} â {time_text} â¢"
    line2 = f"â¢ {h_text} â {g_text} â¢"
    return f"                    {line1}\n        {line2}"


def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Ø§ÙÙØ±Ø¢Ù Ø§ÙÙØ±ÙÙ", callback_data="quran_menu"),
        ],
        [
            InlineKeyboardButton("Ø§ÙØ§Ø°ÙØ§Ø± Ø§ÙÙÙÙÙØ©", callback_data="azkar_daily"),
            InlineKeyboardButton("Ø¯Ø¹Ø§Ø¡", callback_data="dua"),
        ],
        [
            InlineKeyboardButton("Ø§Ø¯Ø¹ÙØ© Ø§ÙØ§ÙØ¨ÙØ§Ø¡", callback_data="dua_nabi"),
            InlineKeyboardButton("Ø¢ÙØ© ÙØ±Ø¢ÙÙØ©", callback_data="ayah"),
        ],
        [
            InlineKeyboardButton("Ø§ÙØ³ÙØ±Ø© Ø§ÙÙØ¨ÙÙØ©", callback_data="prophets_menu"),
            InlineKeyboardButton("ÙØµØ© ØµØ­Ø§Ø¨Ù", callback_data="sahabi"),
        ],
        [
            InlineKeyboardButton("ÙØµØ© ÙØ±Ø¢ÙÙØ©", callback_data="quran_story"),
            InlineKeyboardButton("Ø§ÙØ¨Ø§ÙÙØ§Øª Ø§ÙØµØ§ÙØ­Ø§Øª", callback_data="baqiyat"),
        ],
        [
            InlineKeyboardButton("ØªØ­ØµÙÙ Ø§ÙÙÙØ³", callback_data="tahseen"),
            InlineKeyboardButton("Ø¢ÙØ© Ø§ÙÙØ±Ø³Ù", callback_data="kursi"),
        ],
        [
            InlineKeyboardButton("Ø­Ø¯ÙØ« ÙØ¨ÙÙ", callback_data="hadith"),
            InlineKeyboardButton("Ø§Ø³ÙØ§Ø¡ Ø§ÙÙÙ Ø§ÙØ­Ø³ÙÙ", callback_data="asma"),
        ],
        [
            InlineKeyboardButton("ÙØ¶Ø§Ø¦Ù Ø§ÙØ§Ø¹ÙØ§Ù", callback_data="fadail"),
            InlineKeyboardButton("Ø§Ø°ÙØ§Ø± Ø¨Ø¹Ø¯ Ø§ÙØµÙØ§Ø©", callback_data="azkar_salah"),
        ],
        [
            InlineKeyboardButton("Ø§ÙØ§Ø³ØªØºÙØ§Ø±", callback_data="istighfar"),
            InlineKeyboardButton("Ø¢Ø¯Ø§Ø¨ Ø§Ø³ÙØ§ÙÙØ©", callback_data="adab"),
        ],
        [
            InlineKeyboardButton("Ø§ÙÙØ§Øª Ø§ÙØµÙØ§Ø©", callback_data="prayer_times"),
        ],
        [
            InlineKeyboardButton("ÙÙØ§Ø© Ø§Ø«Ø±", url="https://t.me/Athar_Atkar"),
        ],
        [
            InlineKeyboardButton("Ø§ÙØ³ØªÙØ±Ø§Ù", url="https://www.instagram.com/1947_1951?igsh=bnA3cXloanFvazJx&utm_source=qr"),
            InlineKeyboardButton("ØªÙÙ ØªÙÙ", url="https://www.tiktok.com/@1947_1951?_r=1&_t=ZS-94zjaTgMqE4"),
        ],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙÙØ§Ø¦ÙØ©", callback_data="menu")]
    ])

def azkar_daily_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Ø§Ø°ÙØ§Ø± Ø§ÙØµØ¨Ø§Ø­", callback_data="sabah")],
        [InlineKeyboardButton("Ø§Ø°ÙØ§Ø± Ø§ÙÙØ³Ø§Ø¡", callback_data="masa")],
        [InlineKeyboardButton("Ø§Ø°ÙØ§Ø± Ø§ÙÙÙÙ", callback_data="nawm")],
        [InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙÙØ§Ø¦ÙØ©", callback_data="menu")],
    ])

def prayer_times_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Ø§ÙÙÙØ§Ø·Ù", callback_data="pt_regions"),
            InlineKeyboardButton("Ø§ÙÙØ¯Ù", callback_data="pt_cities"),
        ],
        [InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙÙØ§Ø¦ÙØ©", callback_data="menu")],
    ])

def regions_keyboard():
    keys = list(SAUDI_REGIONS.keys())
    buttons = []
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(SAUDI_REGIONS[keys[i]]["name"], callback_data=f"pt_{keys[i]}")]
        if i + 1 < len(keys):
            row.append(InlineKeyboardButton(SAUDI_REGIONS[keys[i+1]]["name"], callback_data=f"pt_{keys[i+1]}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Ø±Ø¬ÙØ¹", callback_data="prayer_times")])
    return InlineKeyboardMarkup(buttons)

def cities_keyboard():
    keys = list(SAUDI_CITIES.keys())
    buttons = []
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(SAUDI_CITIES[keys[i]]["name"], callback_data=f"pt_{keys[i]}")]
        if i + 1 < len(keys):
            row.append(InlineKeyboardButton(SAUDI_CITIES[keys[i+1]]["name"], callback_data=f"pt_{keys[i+1]}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("Ø±Ø¬ÙØ¹", callback_data="prayer_times")])
    return InlineKeyboardMarkup(buttons)

def prophets_keyboard_page1():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Ø¢Ø¯Ù", callback_data="prophet_adam"),
            InlineKeyboardButton("Ø§Ø¯Ø±ÙØ³", callback_data="prophet_idris"),
            InlineKeyboardButton("ÙÙØ­", callback_data="prophet_nuh"),
        ],
        [
            InlineKeyboardButton("ÙÙØ¯", callback_data="prophet_hud"),
            InlineKeyboardButton("ØµØ§ÙØ­", callback_data="prophet_salih"),
            InlineKeyboardButton("Ø§Ø¨Ø±Ø§ÙÙÙ", callback_data="prophet_ibrahim"),
        ],
        [
            InlineKeyboardButton("ÙÙØ·", callback_data="prophet_lut"),
            InlineKeyboardButton("Ø§Ø³ÙØ§Ø¹ÙÙ", callback_data="prophet_ismail"),
            InlineKeyboardButton("Ø§Ø³Ø­Ø§Ù", callback_data="prophet_ishaq"),
        ],
        [
            InlineKeyboardButton("ÙØ¹ÙÙØ¨", callback_data="prophet_yaqub"),
            InlineKeyboardButton("ÙÙØ³Ù", callback_data="prophet_yusuf"),
            InlineKeyboardButton("Ø´Ø¹ÙØ¨", callback_data="prophet_shuaib"),
        ],
        [
            InlineKeyboardButton("Ø§ÙØªØ§ÙÙ â", callback_data="prophets_page2"),
            InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙÙØ§Ø¦ÙØ©", callback_data="menu"),
        ],
    ])

def prophets_keyboard_page2():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("ÙÙØ³Ù", callback_data="prophet_musa"),
            InlineKeyboardButton("ÙØ§Ø±ÙÙ", callback_data="prophet_harun"),
            InlineKeyboardButton("Ø¯Ø§ÙØ¯", callback_data="prophet_dawud"),
        ],
        [
            InlineKeyboardButton("Ø³ÙÙÙØ§Ù", callback_data="prophet_sulaiman"),
            InlineKeyboardButton("Ø§ÙÙØ§Ø³", callback_data="prophet_ilyas"),
            InlineKeyboardButton("Ø§ÙÙØ³Ø¹", callback_data="prophet_alyasa"),
        ],
        [
            InlineKeyboardButton("Ø°Ù Ø§ÙÙÙÙ", callback_data="prophet_dhulkifl"),
            InlineKeyboardButton("ÙÙÙØ³", callback_data="prophet_yunus"),
            InlineKeyboardButton("Ø²ÙØ±ÙØ§", callback_data="prophet_zakariya"),
        ],
        [
            InlineKeyboardButton("ÙØ­ÙÙ", callback_data="prophet_yahya"),
            InlineKeyboardButton("Ø¹ÙØ³Ù", callback_data="prophet_isa"),
            InlineKeyboardButton("ÙØ­ÙØ¯ ï·º", callback_data="prophet_muhammad"),
        ],
        [
            InlineKeyboardButton("â Ø§ÙØ³Ø§Ø¨Ù", callback_data="prophets_page1"),
            InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙÙØ§Ø¦ÙØ©", callback_data="menu"),
        ],
    ])

NAMES_PER_PAGE = 12

def asma_keyboard(page=0):
    total_pages = (len(ALLAH_NAMES) + NAMES_PER_PAGE - 1) // NAMES_PER_PAGE
    start = page * NAMES_PER_PAGE
    end = min(start + NAMES_PER_PAGE, len(ALLAH_NAMES))
    buttons = []
    for i in range(start, end, 3):
        row = []
        for j in range(i, min(i + 3, end)):
            num = j + 1
            row.append(InlineKeyboardButton(f"{num}. {ALLAH_NAMES[j]['name']}", callback_data=f"asma_{j}"))
        buttons.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("â Ø§ÙØ³Ø§Ø¨Ù", callback_data=f"asma_p{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Ø§ÙØªØ§ÙÙ â", callback_data=f"asma_p{page+1}"))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙÙØ§Ø¦ÙØ©", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)

SURAHS_PER_PAGE = 12

def quran_keyboard(page=0):
    total_pages = (len(QURAN_SURAHS) + SURAHS_PER_PAGE - 1) // SURAHS_PER_PAGE
    start = page * SURAHS_PER_PAGE
    end = min(start + SURAHS_PER_PAGE, len(QURAN_SURAHS))
    buttons = []
    for i in range(start, end, 3):
        row = []
        for j in range(i, min(i + 3, end)):
            surah_num = j + 1
            name = QURAN_SURAHS[j]
            url = f"https://quran.com/ar/{surah_num}"
            row.append(InlineKeyboardButton(f"{surah_num}. {name}", url=url))
        buttons.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("â Ø§ÙØ³Ø§Ø¨Ù", callback_data=f"quran_p{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Ø§ÙØªØ§ÙÙ â", callback_data=f"quran_p{page+1}"))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙÙØ§Ø¦ÙØ©", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)

SEPARATOR_LINE = "âââ â¢ âââ â¨ âââ â¢ âââ"

def get_separator():
    now = datetime.datetime.now(TIMEZONE)
    hijri = Gregorian(now.year, now.month, now.day).to_hijri()
    h_text = f"{hijri.day} {HIJRI_MONTHS[hijri.month]} {hijri.year} ÙÙ"
    g_text = f"{now.day} {GREGORIAN_MONTHS[now.month]} {now.year} Ù"
    day_name = DAYS_AR.get(now.weekday(), "")
    time_text = now.strftime("%I:%M %p").replace("AM", "Øµ").replace("PM", "Ù")
    return f"{h_text} â {day_name}\n{SEPARATOR_LINE}\n{g_text} â {time_text}"

def footer_msg():
    return f"""ÙØ§ ØªÙØ³ÙÙ ØªØ¯Ø¹ÙÙ ÙÙ Ø¬Ø¯Ù ÙØ¬Ø¯ØªÙ ÙÙØ¬ÙÙØ¹ Ø§ÙÙØ§Øª Ø§ÙÙØ³ÙÙÙÙ Ø¨Ø§ÙØ±Ø­ÙØ© ÙØ§ÙÙØºÙØ±Ø©.. Ø§ÙÙÙÙ Ø§Ø¬Ø¹Ù ÙÙØ±ÙÙØ§ ÙØ§ ÙÙØ·ÙØ¦ ÙØ§Ø¬ÙØ¹ÙØ§ Ø¨ÙÙ ÙÙ Ø¬ÙØ§Øª Ø§ÙÙØ¹ÙÙ ð¤

{get_date_line()}"""


async def send_to_channel(bot: Bot, text: str, image_filename: str = None, parse_mode: str = None, send_separator: bool = False):
    image_path = os.path.join(IMAGES_DIR, image_filename) if image_filename else None
    full_text = f"{text}\n\n{get_date_line()}"
    try:
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as photo:
                await bot.send_photo(
                    chat_id=CHANNEL_ID, photo=photo,
                    caption=full_text, parse_mode=parse_mode
                )
        else:
            await bot.send_message(
                chat_id=CHANNEL_ID, text=full_text,
                parse_mode=parse_mode, disable_web_page_preview=True
            )
        if send_separator:
            await bot.send_message(chat_id=CHANNEL_ID, text=get_separator())
    except TelegramError as e:
        logger.error(f"Failed to send to channel: {e}")


async def job_morning_azkar(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending morning azkar...")
    await send_to_channel(context.bot, MORNING_AZKAR_TEXT, "morning.jpg", send_separator=True)

async def job_evening_azkar(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending evening azkar...")
    await send_to_channel(context.bot, EVENING_AZKAR_TEXT, "evening.jpg", send_separator=True)

async def job_sleep_azkar(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending sleep azkar...")
    await send_to_channel(context.bot, SLEEP_AZKAR_TEXT, "sleep.jpg", send_separator=True)

async def job_salawat(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending Salawat...")
    await send_to_channel(context.bot, SALAWAT_TEXT, "salawat.jpg", send_separator=True)

async def job_istijaba(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending Istijaba...")
    await send_to_channel(context.bot, ISTIJABA_TEXT, "istijaba.jpg", send_separator=True)

async def job_social(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending social links...")
    await send_to_channel(context.bot, SOCIAL_TEXT, parse_mode="HTML", send_separator=True)

async def job_kahf(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Sending Surah Al-Kahf reminder...")
    await send_to_channel(context.bot, KAHF_TEXT, parse_mode="HTML", send_separator=True)

async def job_prayer_alert(context: ContextTypes.DEFAULT_TYPE):
    prayer_key = context.job.data
    logger.info(f"Sending prayer alert for {prayer_key}...")
    text = get_single_prayer_text(prayer_key)
    await send_to_channel(context.bot, text, send_separator=True)

async def job_schedule_prayer_alerts(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Scheduling today's prayer alerts...")
    makkah_times = fetch_prayer_times("Makkah")
    if not makkah_times:
        logger.error("Could not fetch prayer times for scheduling")
        return

    now = datetime.datetime.now(TIMEZONE)

    for old_job in context.job_queue.get_jobs_by_name("prayer_alert"):
        old_job.schedule_removal()

    for prayer_key in PRAYER_NAMES_ORDER:
        time_str = makkah_times[prayer_key]
        hour, minute = map(int, time_str.split(":"))
        prayer_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        if prayer_dt > now:
            delay = (prayer_dt - now).total_seconds()
            context.job_queue.run_once(
                job_prayer_alert,
                when=delay,
                data=prayer_key,
                name="prayer_alert"
            )
            logger.info(f"Scheduled {prayer_key} alert at {time_str}")
        else:
            logger.info(f"Skipped {prayer_key} â already passed ({time_str})")

async def job_daily_story(context: ContextTypes.DEFAULT_TYPE):
    import random
    from content import get_random_nabiy, get_random_sahabi, get_random_quran_story
    funcs = [get_random_nabiy, get_random_sahabi, get_random_quran_story]
    story = random.choice(funcs)()
    logger.info("Sending daily story...")
    await send_to_channel(context.bot, story, send_separator=True)

async def job_daily_quiz(context: ContextTypes.DEFAULT_TYPE):
    quiz = get_random_quiz()
    logger.info("Sending daily quiz...")
    try:
        question_text = f"Ø³Ø¤Ø§Ù Ø§ÙÙÙÙ ð¤\n\n{quiz['q']}"
        await context.bot.send_poll(
            chat_id=CHANNEL_ID,
            question=question_text,
            options=quiz["options"],
            type="quiz",
            correct_option_id=quiz["correct"],
            is_anonymous=True
        )
    except TelegramError as e:
        logger.error(f"Failed to send quiz: {e}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=main_keyboard()
    )

async def cmd_athar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        HELP_TEXT,
        reply_markup=main_keyboard()
    )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    handlers = {
        "sabah": get_random_azkar_sabah,
        "masa": get_random_azkar_masa,
        "nawm": get_random_azkar_nawm,
        "dua": get_random_dua,
        "dua_nabi": get_random_dua_nabi,
        "qissa": get_random_nabiy,
        "sahabi": get_random_sahabi,
        "quran_story": get_random_quran_story,
        "ayah": get_random_ayah,
        "hadith": get_random_hadith,
        "fadail": get_random_fadl,
        "azkar_salah": get_random_azkar_salah,
        "istighfar": get_random_istighfar,
        "adab": get_random_adab,
    }

    if data == "menu":
        await query.message.reply_text(HELP_TEXT, reply_markup=main_keyboard())
    elif data == "azkar_daily":
        await query.message.reply_text("Ø§ÙØ§Ø°ÙØ§Ø± Ø§ÙÙÙÙÙØ© ð¤\n\nØ§Ø®ØªØ±:", reply_markup=azkar_daily_keyboard())
    elif data in ("sabah", "masa", "nawm"):
        funcs = {"sabah": get_random_azkar_sabah, "masa": get_random_azkar_masa, "nawm": get_random_azkar_nawm}
        text = funcs[data]()
        await query.message.reply_text(text)
        await query.message.reply_text(get_separator())
        await query.message.reply_text(footer_msg(), reply_markup=azkar_daily_keyboard())
        return
    elif data == "quran_menu":
        await query.message.reply_text("Ø§ÙÙØ±Ø¢Ù Ø§ÙÙØ±ÙÙ ð¤\n\nØ§Ø®ØªØ± Ø§ÙØ³ÙØ±Ø© ÙÙØ±Ø§Ø¡ØªÙØ§:", reply_markup=quran_keyboard(0))
    elif data.startswith("quran_p"):
        page = int(data[7:])
        await query.message.reply_text("Ø§ÙÙØ±Ø¢Ù Ø§ÙÙØ±ÙÙ ð¤\n\nØ§Ø®ØªØ± Ø§ÙØ³ÙØ±Ø© ÙÙØ±Ø§Ø¡ØªÙØ§:", reply_markup=quran_keyboard(page))
    elif data == "asma":
        await query.message.reply_text("Ø§Ø³ÙØ§Ø¡ Ø§ÙÙÙ Ø§ÙØ­Ø³ÙÙ ð¤\n\nØ§Ø®ØªØ± Ø§Ø³ÙØ§ ÙÙØ¹Ø±ÙØ© ÙØ¹ÙØ§Ù:", reply_markup=asma_keyboard(0))
    elif data.startswith("asma_p"):
        page = int(data[6:])
        await query.message.reply_text("Ø§Ø³ÙØ§Ø¡ Ø§ÙÙÙ Ø§ÙØ­Ø³ÙÙ ð¤\n\nØ§Ø®ØªØ± Ø§Ø³ÙØ§ ÙÙØ¹Ø±ÙØ© ÙØ¹ÙØ§Ù:", reply_markup=asma_keyboard(page))
    elif data.startswith("asma_") and not data.startswith("asma_p"):
        idx = int(data[5:])
        if 0 <= idx < len(ALLAH_NAMES):
            entry = ALLAH_NAMES[idx]
            page = idx // NAMES_PER_PAGE
            text = f"{idx+1}. {entry['name']} ð¤\n\n{entry['meaning']}"
            await query.message.reply_text(text)
            await query.message.reply_text(get_separator())
            await query.message.reply_text(footer_msg(), reply_markup=asma_keyboard(page))
        return
    elif data == "noop":
        await query.answer()
        return
    elif data == "prophets_menu" or data == "prophets_page1":
        await query.message.reply_text("Ø§ÙØ³ÙØ±Ø© Ø§ÙÙØ¨ÙÙØ© ð¤\n\nØ§Ø®ØªØ± ÙØ¨ÙØ§ ÙÙØ±Ø§Ø¡Ø© Ø³ÙØ±ØªÙ:", reply_markup=prophets_keyboard_page1())
    elif data == "prophets_page2":
        await query.message.reply_text("Ø§ÙØ³ÙØ±Ø© Ø§ÙÙØ¨ÙÙØ© ð¤\n\nØ§Ø®ØªØ± ÙØ¨ÙØ§ ÙÙØ±Ø§Ø¡Ø© Ø³ÙØ±ØªÙ:", reply_markup=prophets_keyboard_page2())
    elif data.startswith("prophet_") and not data.startswith("prophet_info_") and data[8:] in PROPHETS:
        prophet_key = data[8:]
        prophet = PROPHETS[prophet_key]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Ø³ÙØ±ØªÙ", callback_data=f"prophet_info_{prophet_key}_story")],
            [InlineKeyboardButton("Ø²ÙØ¬Ø§ØªÙ", callback_data=f"prophet_info_{prophet_key}_wives")],
            [InlineKeyboardButton("Ø£ÙÙØ§Ø¯Ù", callback_data=f"prophet_info_{prophet_key}_children")],
            [InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙØ£ÙØ¨ÙØ§Ø¡", callback_data="prophets_page1" if prophet_key in list(PROPHETS.keys())[:12] else "prophets_page2")],
            [InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙÙØ§Ø¦ÙØ©", callback_data="menu")],
        ])
        await query.message.reply_text(f"{prophet['name']} ð¤\n\nØ§Ø®ØªØ± ÙØ§ ØªØ±ÙØ¯ ÙØ¹Ø±ÙØªÙ:", reply_markup=keyboard)
    elif data.startswith("prophet_info_"):
        parts = data[len("prophet_info_"):].rsplit("_", 1)
        prophet_key = parts[0]
        info_type = parts[1]
        if prophet_key in PROPHETS and info_type in ("story", "wives", "children"):
            prophet = PROPHETS[prophet_key]
            text = prophet.get(info_type, "ÙØ§ ØªÙØ¬Ø¯ ÙØ¹ÙÙÙØ§Øª ÙØªÙÙØ±Ø©")
            await query.message.reply_text(text)
            await query.message.reply_text(get_separator())
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Ø³ÙØ±ØªÙ", callback_data=f"prophet_info_{prophet_key}_story")],
                [InlineKeyboardButton("Ø²ÙØ¬Ø§ØªÙ", callback_data=f"prophet_info_{prophet_key}_wives")],
                [InlineKeyboardButton("Ø£ÙÙØ§Ø¯Ù", callback_data=f"prophet_info_{prophet_key}_children")],
                [InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙØ£ÙØ¨ÙØ§Ø¡", callback_data="prophets_page1" if prophet_key in list(PROPHETS.keys())[:12] else "prophets_page2")],
                [InlineKeyboardButton("Ø±Ø¬ÙØ¹ ÙÙÙØ§Ø¦ÙØ©", callback_data="menu")],
            ])
            await query.message.reply_text(footer_msg(), reply_markup=keyboard)
    elif data == "prayer_times":
        await query.message.reply_text("Ø§ÙÙØ§Øª Ø§ÙØµÙØ§Ø© ð¤\n\nØ§Ø®ØªØ± Ø§ÙÙÙØ§Ø·Ù Ø§Ù Ø§ÙÙØ¯Ù:", reply_markup=prayer_times_keyboard())
    elif data == "pt_regions":
        await query.message.reply_text("Ø§Ø®ØªØ± Ø§ÙÙÙØ·ÙØ© ð¤", reply_markup=regions_keyboard())
    elif data == "pt_cities":
        await query.message.reply_text("Ø§Ø®ØªØ± Ø§ÙÙØ¯ÙÙØ© ð¤", reply_markup=cities_keyboard())
    elif data.startswith("pt_") and data[3:] in {**SAUDI_REGIONS, **SAUDI_CITIES}:
        location_key = data[3:]
        text = get_prayer_times_for_location(location_key)
        await query.message.reply_text(text)
        await query.message.reply_text(get_separator())
        await query.message.reply_text(footer_msg(), reply_markup=prayer_times_keyboard())
    elif data == "kursi":
        await query.message.reply_text(AYAT_KURSI)
        await query.message.reply_text(get_separator())
        await query.message.reply_text(footer_msg(), reply_markup=back_keyboard())
    elif data == "baqiyat":
        await query.message.reply_text(BAQIYAT)
        await query.message.reply_text(get_separator())
        await query.message.reply_text(footer_msg(), reply_markup=back_keyboard())
    elif data == "tahseen":
        await query.message.reply_text(get_random_tahseen())
        await query.message.reply_text(get_separator())
        await query.message.reply_text(footer_msg(), reply_markup=back_keyboard())
    elif data in handlers:
        text = handlers[data]()
        await query.message.reply_text(text)
        await query.message.reply_text(get_separator())
        await query.message.reply_text(footer_msg(), reply_markup=back_keyboard())
    else:
        await query.message.reply_text(HELP_TEXT, reply_markup=main_keyboard())


def _strip(text):
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


SPECIAL_VERSES = {
    "Ø¢ÙØ© Ø§ÙÙØ±Ø³Ù": "KURSI",
    "Ø§ÙØ© Ø§ÙÙØ±Ø³Ù": "KURSI",
    "Ø®ÙØ§ØªÙÙ Ø§ÙØ¨ÙØ±Ø©": "KHAWATIM",
    "Ø®ÙØ§ØªÙÙ Ø³ÙØ±Ø© Ø§ÙØ¨ÙØ±Ø©": "KHAWATIM",
    "Ø®ÙØ§ØªÙÙ Ø§ÙØ¨ÙØ±Ù": "KHAWATIM",
}


ADMIN_IDS = []

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    msg = update.message.text.strip()
    clean = _strip(msg)

    links_in_msg = msg.strip().split()
    tiktok_links = [l for l in links_in_msg if "tiktok.com" in l]
    insta_links = [l for l in links_in_msg if "instagram.com" in l]
    all_social_links = tiktok_links + insta_links

    if all_social_links:
        user_id = update.message.from_user.id if update.message.from_user else None
        if not ADMIN_IDS or (user_id and user_id in ADMIN_IDS):
            download_link = tiktok_links[0] if tiktok_links else insta_links[0]
            if tiktok_links and insta_links:
                platform = "Ø§ÙØ§ÙØ³ØªÙØ±Ø§Ù ÙØ§ÙØªÙÙ ØªÙÙ"
            elif tiktok_links:
                platform = "ØªÙÙ ØªÙÙ"
            else:
                platform = "Ø§ÙØ³ØªÙØ±Ø§Ù"

            link_parts = []
            for l in all_social_links:
                if "tiktok" in l:
                    link_parts.append(f'<a href="{l}">ØªÙÙ ØªÙÙ</a>')
                else:
                    link_parts.append(f'<a href="{l}">Ø§ÙØ³ØªÙØ±Ø§Ù</a>')
            links_text = " â ".join(link_parts)
            caption = f"""ÙÙØ·Ø¹ Ø¬Ø¯ÙØ¯ Ø¹ÙÙ {platform} ð¤

ÙØ§ ØªÙØ³ÙÙ ØªØ¯Ø¹ÙÙ ÙÙ Ø¬Ø¯Ù ÙØ¬Ø¯ØªÙ ÙÙØ¬ÙÙØ¹ Ø§ÙÙØ§Øª Ø§ÙÙØ³ÙÙÙÙ ð¤

{links_text}

{get_date_line()}"""
            wait_msg = await update.message.reply_text("Ø¬Ø§Ø±Ù ØªØ­ÙÙÙ Ø§ÙÙÙØ·Ø¹... ð¤")
            video_path = None
            try:
                import yt_dlp
                import tempfile
                tmp_dir = tempfile.mkdtemp()
                video_path = os.path.join(tmp_dir, "video.mp4")
                ydl_opts = {
                    "outtmpl": video_path,
                    "format": "best[ext=mp4]/best",
                    "quiet": True,
                    "no_warnings": True,
                    "socket_timeout": 30,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([download_link])

                if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                    with open(video_path, "rb") as vf:
                        await context.bot.send_video(
                            chat_id=CHANNEL_ID,
                            video=vf,
                            caption=caption,
                            parse_mode="HTML",
                            supports_streaming=True
                        )
                    await wait_msg.edit_text("ØªÙ ÙØ´Ø± Ø§ÙÙÙØ·Ø¹ ÙÙ Ø§ÙÙÙØ§Ø© ð¤")
                else:
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=caption,
                        parse_mode="HTML",
                        disable_web_page_preview=False
                    )
                    await wait_msg.edit_text("ØªÙ ÙØ´Ø± Ø§ÙØ±Ø§Ø¨Ø· ÙÙ Ø§ÙÙÙØ§Ø© ð¤")
            except Exception as e:
                logger.warning(f"Video download failed: {e}")
                try:
                    await context.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=caption,
                        parse_mode="HTML",
                        disable_web_page_preview=False
                    )
                    await wait_msg.edit_text("ØªÙ ÙØ´Ø± Ø§ÙØ±Ø§Ø¨Ø· ÙÙ Ø§ÙÙÙØ§Ø© ð¤")
                except TelegramError as te:
                    await wait_msg.edit_text(f"ÙØ§ ÙØ¯Ø±Øª Ø§ÙØ´Ø± Ø§ÙÙÙØ·Ø¹: {te}")
            finally:
                if video_path and os.path.exists(video_path):
                    os.remove(video_path)
            return

    if msg in ("Ø§ÙÙØ§Øª Ø§ÙØµÙØ§Ø©", "Ø£ÙÙØ§Øª Ø§ÙØµÙØ§Ø©", "Ø§ÙØµÙØ§Ø©", "ÙÙØ§ÙÙØª Ø§ÙØµÙØ§Ø©"):
        text = get_prayer_times_text()
        await update.message.reply_text(text)
        await update.message.reply_text(get_separator())
        await update.message.reply_text(footer_msg(), reply_markup=back_keyboard())
        return

    if msg in ("Ø§Ø«Ø±", "Ø£Ø«Ø±", "Ø§ÙÙØ§Ø¦ÙØ©", "Ø§ÙÙØ³Ø§Ø¹Ø¯Ø©"):
        await update.message.reply_text(HELP_TEXT, reply_markup=main_keyboard())
        return

    simple_map = {
        ("Ø§Ø°ÙØ§Ø±", "Ø£Ø°ÙØ§Ø±", "Ø°ÙØ±"): get_random_azkar,
        ("Ø§Ø°ÙØ§Ø± Ø§ÙØµØ¨Ø§Ø­", "Ø£Ø°ÙØ§Ø± Ø§ÙØµØ¨Ø§Ø­", "ØµØ¨Ø§Ø­"): get_random_azkar_sabah,
        ("Ø§Ø°ÙØ§Ø± Ø§ÙÙØ³Ø§Ø¡", "Ø£Ø°ÙØ§Ø± Ø§ÙÙØ³Ø§Ø¡", "ÙØ³Ø§Ø¡"): get_random_azkar_masa,
        ("Ø§Ø°ÙØ§Ø± Ø§ÙÙÙÙ", "Ø£Ø°ÙØ§Ø± Ø§ÙÙÙÙ", "ÙÙÙ"): get_random_azkar_nawm,
        ("Ø¯Ø¹Ø§Ø¡", "Ø§Ø¯Ø¹ÙØ©", "Ø£Ø¯Ø¹ÙØ©", "Ø¯Ø¹ÙØ©"): get_random_dua,
        ("ÙØµØ©", "ÙØµØµ", "Ø§ÙØ¨ÙØ§Ø¡", "Ø£ÙØ¨ÙØ§Ø¡", "ÙØ¨Ù"): get_random_nabiy,
        ("Ø¢ÙØ©", "Ø§ÙØ©", "ÙØ±Ø¢Ù", "ÙØ±Ø§Ù"): get_random_ayah,
        ("ØµØ­Ø§Ø¨Ø©", "ØµØ­Ø§Ø¨Ù", "ØµØ­Ø§Ø¨Ù"): get_random_sahabi,
        ("ÙØµØ© ÙØ±Ø¢ÙÙØ©", "ÙØµØµ Ø§ÙÙØ±Ø¢Ù", "ÙØµÙ ÙØ±Ø¢ÙÙÙ", "ÙØµØµ ÙØ±Ø§ÙÙÙ"): get_random_quran_story,
        ("Ø§Ø¯Ø¹ÙØ© Ø§ÙØ§ÙØ¨ÙØ§Ø¡", "Ø¯Ø¹Ø§Ø¡ Ø§ÙØ§ÙØ¨ÙØ§Ø¡", "Ø¯Ø¹Ø§Ø¡ ÙØ¨Ù", "Ø§Ø¯Ø¹ÙÙ Ø§ÙØ§ÙØ¨ÙØ§Ø¡"): get_random_dua_nabi,
        ("ØªØ­ØµÙÙ", "ØªØ­ØµÙÙ Ø§ÙÙÙØ³", "ØªØ­ØµÙ"): get_random_tahseen,
        ("Ø­Ø¯ÙØ«", "Ø§Ø­Ø§Ø¯ÙØ«", "Ø­Ø¯ÙØ« ÙØ¨ÙÙ", "Ø£Ø­Ø§Ø¯ÙØ«"): get_random_hadith,
        ("Ø§Ø³ÙØ§Ø¡ Ø§ÙÙÙ", "Ø§Ø³ÙØ§Ø¡ Ø§ÙÙÙ Ø§ÙØ­Ø³ÙÙ", "Ø£Ø³ÙØ§Ø¡ Ø§ÙÙÙ"): get_random_asma,
        ("ÙØ¶Ø§Ø¦Ù", "ÙØ¶Ø§Ø¦Ù Ø§ÙØ§Ø¹ÙØ§Ù", "ÙØ¶Ù"): get_random_fadl,
        ("Ø§Ø°ÙØ§Ø± Ø§ÙØµÙØ§Ø©", "Ø§Ø°ÙØ§Ø± Ø¨Ø¹Ø¯ Ø§ÙØµÙØ§Ø©", "Ø¨Ø¹Ø¯ Ø§ÙØµÙØ§Ø©"): get_random_azkar_salah,
        ("Ø§Ø³ØªØºÙØ§Ø±", "Ø§Ø³ØªØºÙØ±", "Ø§ÙØ§Ø³ØªØºÙØ§Ø±"): get_random_istighfar,
        ("Ø¢Ø¯Ø§Ø¨", "Ø§Ø¯Ø§Ø¨", "Ø¢Ø¯Ø§Ø¨ Ø§Ø³ÙØ§ÙÙØ©", "Ø§Ø¯Ø§Ø¨ Ø§Ø³ÙØ§ÙÙÙ"): get_random_adab,
    }

    for keys, func in simple_map.items():
        if msg in keys or clean in keys:
            await update.message.reply_text(func())
            await update.message.reply_text(get_separator())
            await update.message.reply_text(footer_msg(), reply_markup=back_keyboard())
            return

    for verse_key, verse_type in SPECIAL_VERSES.items():
        if clean == verse_key or clean == _strip(verse_key):
            if verse_type == "KURSI":
                await update.message.reply_text(AYAT_KURSI)
            elif verse_type == "KHAWATIM":
                await update.message.reply_text(KHAWATIM_BAQARA)
            await update.message.reply_text(get_separator())
            await update.message.reply_text(footer_msg(), reply_markup=back_keyboard())
            return

    if len(msg) > 3:
        user_id = update.message.from_user.id if update.message.from_user else None
        try:
        answer = ask_islamic_question(msg, user_id=user_id)
    except:
        answer = None
        if answer:
            await update.message.reply_text(answer)
            await update.message.reply_text(get_separator())
            await update.message.reply_text(footer_msg(), reply_markup=back_keyboard())
        else:
            await update.message.reply_text(
                "ÙÙ Ø§ØªÙÙÙ ÙÙ Ø§ÙØ§Ø¬Ø§Ø¨Ø© Ø­Ø§ÙÙØ§ â Ø­Ø§ÙÙ ÙØ±Ø© Ø§Ø®Ø±Ù ð¤",
                reply_markup=back_keyboard()
            )


async def _delete_msgs(context: ContextTypes.DEFAULT_TYPE, chat_id, msg_id1, msg_id2):
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id1)
        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id2)
        logger.info("Deleted welcome messages from channel")
    except TelegramError as e:
        logger.warning(f"Could not delete welcome messages: {e}")


def channel_welcome():
    return f"""ÙÙØ±ØªÙØ§ Ø¨ÙÙ Ø§ÙÙÙ ÙÙØ§Ø³Ù ð¤

ÙÙØ§ ÙÙØ§ÙÙ ÙÙØ­Ø·ØªÙ ÙÙÙØ¯ÙØ¡ ÙØ·ÙØ£ÙÙÙØ© Ø§ÙÙÙØ¨

ÙØ¬ÙØ¯Ù ÙØ¹ÙØ§ ÙÙ ÙØ¬Ø±Ø¯ Ø±ÙÙ ÙÙ "Ø§Ø«Ø±" Ø·ÙØ¨ ÙØ¬ÙØ¹ÙØ§ Ø¹ÙÙ Ø°ÙØ± Ø§ÙÙÙ ÙÙØµØµ Ø§ÙØ®ÙØ±

ØµØ¯ÙØ© Ø¬Ø§Ø±ÙØ© Ø¹Ù Ø¬Ø¯Ù ÙØ¬Ø¯ØªÙ ÙÙØ¬ÙÙØ¹ Ø§ÙÙØ§Øª Ø§ÙÙØ³ÙÙÙÙ ð«¶ð»

{get_date_line()}"""


async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.chat_member:
        return
    member = update.chat_member
    if member.new_chat_member.status in ("member", "creator", "administrator"):
        if member.old_chat_member.status in ("left", "kicked"):
            user = member.new_chat_member.user
            name = user.first_name or ""
            try:
                welcome_msg = await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=channel_welcome()
                )
                social_msg = await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=SOCIAL_TEXT,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                logger.info(f"Sent channel welcome + social for new member: {user.id}")
                context.job_queue.run_once(
                    lambda ctx, cid=CHANNEL_ID, mid1=welcome_msg.message_id, mid2=social_msg.message_id: _delete_msgs(ctx, cid, mid1, mid2),
                    when=120,
                    name=f"delete_welcome_{user.id}"
                )
            except TelegramError as e:
                logger.warning(f"Could not send channel welcome: {e}")


def build_application() -> Application:
    if not TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_athar))
    app.add_handler(CommandHandler("athar", cmd_athar))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(ChatMemberHandler(handle_new_member, ChatMemberHandler.CHAT_MEMBER))

    jq = app.job_queue

    jq.run_daily(
        job_morning_azkar,
        time=datetime.time(5, 15, tzinfo=TIMEZONE),
        name="Ø§Ø°ÙØ§Ø± Ø§ÙØµØ¨Ø§Ø­"
    )

    jq.run_daily(
        job_evening_azkar,
        time=datetime.time(18, 30, tzinfo=TIMEZONE),
        name="Ø§Ø°ÙØ§Ø± Ø§ÙÙØ³Ø§Ø¡"
    )

    jq.run_daily(
        job_sleep_azkar,
        time=datetime.time(21, 30, tzinfo=TIMEZONE),
        name="Ø§Ø°ÙØ§Ø± Ø§ÙÙÙÙ"
    )

    jq.run_daily(
        job_salawat,
        time=datetime.time(8, 30, tzinfo=TIMEZONE),
        days=(5,),
        name="Ø§ÙØµÙØ§Ø© Ø¹ÙÙ Ø§ÙÙØ¨Ù"
    )

    jq.run_daily(
        job_kahf,
        time=datetime.time(8, 30, tzinfo=TIMEZONE),
        days=(5,),
        name="Ø³ÙØ±Ø© Ø§ÙÙÙÙ"
    )

    jq.run_daily(
        job_istijaba,
        time=datetime.time(16, 30, tzinfo=TIMEZONE),
        days=(5,),
        name="Ø³Ø§Ø¹Ø© Ø§ÙØ§Ø³ØªØ¬Ø§Ø¨Ø©"
    )

    jq.run_daily(
        job_social,
        time=datetime.time(20, 0, tzinfo=TIMEZONE),
        days=(5,),
        name="Ø­Ø³Ø§Ø¨Ø§Øª Ø§ÙØªÙØ§ØµÙ"
    )

    jq.run_daily(
        job_schedule_prayer_alerts,
        time=datetime.time(1, 0, tzinfo=TIMEZONE),
        name="Ø¬Ø¯ÙÙØ© ØªÙØ¨ÙÙØ§Øª Ø§ÙØµÙØ§Ø©"
    )

    jq.run_once(
        job_schedule_prayer_alerts,
        when=5,
        name="Ø¬Ø¯ÙÙØ© ØªÙØ¨ÙÙØ§Øª Ø§ÙØµÙØ§Ø© Ø§ÙØ¢Ù"
    )

    jq.run_daily(
        job_daily_story,
        time=datetime.time(16, 0, tzinfo=TIMEZONE),
        name="ÙØµØ© ÙÙÙÙØ©"
    )

    jq.run_daily(
        job_daily_quiz,
        time=datetime.time(14, 0, tzinfo=TIMEZONE),
        name="Ø³Ø¤Ø§Ù ÙÙÙÙ"
    )

    logger.info("Application built with all handlers and scheduled jobs.")
    return app

if __name__ == "__main__":
    import asyncio
    application = build_application()
    print("Ø§ÙØ¨ÙØª Ø¨Ø¯Ø£ Ø§ÙØ¹ÙÙ Ø§ÙØ¢Ù... ð")
    application.run_polling(drop_pending_updates=True, close_loop=False)


def ask_islamic_question(question, user_id=None):
    try:
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

    try:
        return "Ø³Ø¤Ø§Ù Ø¬ÙÙÙ ð¤\nÙÙÙ Ø­Ø§ÙÙØ§Ù ÙØ§ Ø¹ÙØ¯Ù Ø¬ÙØ§Ø¨ Ø¯ÙÙÙ.\nØ¬Ø±Ø¨ ØªØ¹ÙØ¯ ØµÙØ§ØºØ© Ø§ÙØ³Ø¤Ø§Ù Ø¨Ø´ÙÙ Ø£ÙØ¶Ø­."
    except:
        return None
