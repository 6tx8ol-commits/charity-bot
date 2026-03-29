import os
import json
import logging
import datetime
import asyncio
import unicodedata
import aiohttp
from zoneinfo import ZoneInfo
from hijridate import Hijri, Gregorian
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

ADMIN_ID = 8466914447
USERS_FILE = "users.json"

def load_users() -> dict:
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_user(user) -> None:
    users = load_users()
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "id": user.id,
            "name": user.full_name,
            "username": f"@{user.username}" if user.username else "—",
            "joined": datetime.datetime.now(ZoneInfo("Asia/Riyadh")).strftime("%Y-%m-%d %H:%M"),
        }
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Could not save user: {e}")

async def cmd_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    users = load_users()
    count = len(users)
    if count == 0:
        await update.message.reply_text("لا يوجد مستخدمون بعد.")
        return
    lines = [f"👥 المستخدمون في بوت أثر: {count}\n"]
    for u in users.values():
        lines.append(f"• {u['name']} {u['username']}\n  انضم: {u['joined']}")
    await update.message.reply_text("\n".join(lines))

TOKEN = os.environ.get("BOT_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemma-3-4b-it:free"

_AI_SHORT_PROMPT = "أنت مساعد إسلامي. أجب في ٢-٣ جمل فقط بالعربية، ركّز على جوهر الجواب فقط باختصار."
_AI_FULL_PROMPT  = """أنت مساعد إسلامي متخصص. أجب بالعربية بشكل مفصّل وشامل.
- استند للقرآن والسنة واذكر المصادر
- للفتاوى الشخصية: انصح بمراجعة عالم
- لا تتكلم في أمور غير دينية"""

_FULL_ANSWER_TRIGGERS = {"الجواب كامل", "جواب كامل", "الكامل", "كامل"}


async def ask_gemini(question: str, full: bool = False) -> str | None:
    if not OPENROUTER_API_KEY:
        return None
    prompt     = _AI_FULL_PROMPT  if full else _AI_SHORT_PROMPT
    max_tokens = 500              if full else 110
    timeout    = 30               if full else 12
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": question},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_URL,
                json=payload,
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as resp:
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.warning(f"OpenRouter error: {e}")
        return None


_raw_channel = os.environ.get("TELEGRAM_CHANNEL_ID", "")
if _raw_channel.startswith("https://t.me/"):
    CHANNEL_ID = "@" + _raw_channel.split("https://t.me/")[-1].strip("/")
elif _raw_channel.startswith("t.me/"):
    CHANNEL_ID = "@" + _raw_channel.split("t.me/")[-1].strip("/")
else:
    CHANNEL_ID = _raw_channel

TIMEZONE = ZoneInfo("Asia/Riyadh")

HIJRI_MONTHS = {
    1: "محرم", 2: "صفر", 3: "ربيع الاول", 4: "ربيع الثاني",
    5: "جمادى الاولى", 6: "جمادى الثانية", 7: "رجب", 8: "شعبان",
    9: "رمضان", 10: "شوال", 11: "ذو القعدة", 12: "ذو الحجة"
}

GREGORIAN_MONTHS = {
    1: "يناير", 2: "فبراير", 3: "مارس", 4: "ابريل",
    5: "مايو", 6: "يونيو", 7: "يوليو", 8: "اغسطس",
    9: "سبتمبر", 10: "اكتوبر", 11: "نوفمبر", 12: "ديسمبر"
}

DAYS_AR = {
    0: "الاثنين", 1: "الثلاثاء", 2: "الاربعاء", 3: "الخميس",
    4: "الجمعة", 5: "السبت", 6: "الاحد"
}

def get_date_line():
    now = datetime.datetime.now(TIMEZONE)
    hijri = Gregorian(now.year, now.month, now.day).to_hijri()
    day_name = DAYS_AR.get(now.weekday(), "")
    h_text = f"{hijri.day} {HIJRI_MONTHS[hijri.month]} {hijri.year} هـ"
    g_text = f"{now.day} {GREGORIAN_MONTHS[now.month]} {now.year} م"
    time_text = now.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    line1 = f"• {day_name} — {time_text} •"
    line2 = f"• {h_text} — {g_text} •"
    return f"                    {line1}\n        {line2}"


def main_keyboard():
    return ReplyKeyboardMarkup([["📋 القائمة"]], resize_keyboard=True)


def main_inline_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 القرآن الكريم", callback_data="quran_menu")],
        [InlineKeyboardButton("🌿 الاذكار اليومية", callback_data="azkar_daily"),
         InlineKeyboardButton("🤲 دعاء", callback_data="dua")],
        [InlineKeyboardButton("🕊️ ادعية الانبياء", callback_data="dua_nabi"),
         InlineKeyboardButton("✨ آية قرآنية", callback_data="ayah")],
        [InlineKeyboardButton("🌙 السيرة النبوية", callback_data="prophets_menu"),
         InlineKeyboardButton("⭐ قصة صحابي", callback_data="sahabi")],
        [InlineKeyboardButton("📜 قصة قرآنية", callback_data="quran_story"),
         InlineKeyboardButton("💎 الباقيات الصالحات", callback_data="baqiyat")],
        [InlineKeyboardButton("🛡️ تحصين النفس", callback_data="tahseen"),
         InlineKeyboardButton("🔵 آية الكرسي", callback_data="kursi")],
        [InlineKeyboardButton("📚 حديث نبوي", callback_data="hadith"),
         InlineKeyboardButton("🌟 اسماء الله الحسنى", callback_data="asma")],
        [InlineKeyboardButton("🌸 فضائل الاعمال", callback_data="fadail"),
         InlineKeyboardButton("🕌 اذكار بعد الصلاة", callback_data="azkar_salah")],
        [InlineKeyboardButton("💫 الاستغفار", callback_data="istighfar"),
         InlineKeyboardButton("🌺 آداب اسلامية", callback_data="adab")],
        [InlineKeyboardButton("🕐 اوقات الصلاة", callback_data="prayer_times")],
        [InlineKeyboardButton("🌐 الموقع الرسمي", url="https://legendary-yeot-b80ee7.netlify.app/"),
         InlineKeyboardButton("📢 قناة اثر", url="https://t.me/Athar_Atkar")],
        [InlineKeyboardButton("📸 انستقرام", url="https://www.instagram.com/1947_1951?igsh=bnA3cXloanFvazJx&utm_source=qr"),
         InlineKeyboardButton("🎬 تيك توك", url="https://www.tiktok.com/@1947_1951?_r=1&_t=ZS-94zjaTgMqE4")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("رجوع للقائمة", callback_data="menu")]
    ])

def azkar_daily_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌅 اذكار الصباح", callback_data="sabah")],
        [InlineKeyboardButton("🌙 اذكار المساء", callback_data="masa")],
        [InlineKeyboardButton("😴 اذكار النوم", callback_data="nawm")],
        [InlineKeyboardButton("رجوع للقائمة", callback_data="menu")],
    ])

def prayer_times_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("المناطق", callback_data="pt_regions"),
            InlineKeyboardButton("المدن", callback_data="pt_cities"),
        ],
        [InlineKeyboardButton("رجوع للقائمة", callback_data="menu")],
    ])

def regions_keyboard():
    keys = list(SAUDI_REGIONS.keys())
    buttons = []
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(SAUDI_REGIONS[keys[i]]["name"], callback_data=f"pt_{keys[i]}")]
        if i + 1 < len(keys):
            row.append(InlineKeyboardButton(SAUDI_REGIONS[keys[i+1]]["name"], callback_data=f"pt_{keys[i+1]}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("رجوع", callback_data="prayer_times")])
    return InlineKeyboardMarkup(buttons)

def cities_keyboard():
    keys = list(SAUDI_CITIES.keys())
    buttons = []
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(SAUDI_CITIES[keys[i]]["name"], callback_data=f"pt_{keys[i]}")]
        if i + 1 < len(keys):
            row.append(InlineKeyboardButton(SAUDI_CITIES[keys[i+1]]["name"], callback_data=f"pt_{keys[i+1]}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("رجوع", callback_data="prayer_times")])
    return InlineKeyboardMarkup(buttons)

def prophets_keyboard_page1():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("آدم", callback_data="prophet_adam"),
            InlineKeyboardButton("ادريس", callback_data="prophet_idris"),
            InlineKeyboardButton("نوح", callback_data="prophet_nuh"),
        ],
        [
            InlineKeyboardButton("هود", callback_data="prophet_hud"),
            InlineKeyboardButton("صالح", callback_data="prophet_salih"),
            InlineKeyboardButton("ابراهيم", callback_data="prophet_ibrahim"),
        ],
        [
            InlineKeyboardButton("لوط", callback_data="prophet_lut"),
            InlineKeyboardButton("اسماعيل", callback_data="prophet_ismail"),
            InlineKeyboardButton("اسحاق", callback_data="prophet_ishaq"),
        ],
        [
            InlineKeyboardButton("يعقوب", callback_data="prophet_yaqub"),
            InlineKeyboardButton("يوسف", callback_data="prophet_yusuf"),
            InlineKeyboardButton("شعيب", callback_data="prophet_shuaib"),
        ],
        [
            InlineKeyboardButton("أيوب", callback_data="prophet_ayyub"),
        ],
        [
            InlineKeyboardButton("التالي ←", callback_data="prophets_page2"),
            InlineKeyboardButton("رجوع للقائمة", callback_data="menu"),
        ],
    ])

def prophets_keyboard_page2():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("موسى", callback_data="prophet_musa"),
            InlineKeyboardButton("هارون", callback_data="prophet_harun"),
            InlineKeyboardButton("داود", callback_data="prophet_dawud"),
        ],
        [
            InlineKeyboardButton("سليمان", callback_data="prophet_sulaiman"),
            InlineKeyboardButton("الياس", callback_data="prophet_ilyas"),
            InlineKeyboardButton("اليسع", callback_data="prophet_alyasa"),
        ],
        [
            InlineKeyboardButton("ذو الكفل", callback_data="prophet_dhulkifl"),
            InlineKeyboardButton("يونس", callback_data="prophet_yunus"),
            InlineKeyboardButton("زكريا", callback_data="prophet_zakariya"),
        ],
        [
            InlineKeyboardButton("يحيى", callback_data="prophet_yahya"),
            InlineKeyboardButton("عيسى", callback_data="prophet_isa"),
            InlineKeyboardButton("محمد ﷺ", callback_data="prophet_muhammad"),
        ],
        [
            InlineKeyboardButton("→ السابق", callback_data="prophets_page1"),
            InlineKeyboardButton("رجوع للقائمة", callback_data="menu"),
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
        nav.append(InlineKeyboardButton("→ السابق", callback_data=f"asma_p{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("التالي ←", callback_data=f"asma_p{page+1}"))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton("رجوع للقائمة", callback_data="menu")])
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
            url = f"https://legendary-yeot-b80ee7.netlify.app/surah.html?s={surah_num}"
            row.append(InlineKeyboardButton(f"{surah_num}. {name}", url=url))
        buttons.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("→ السابق", callback_data=f"quran_p{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("التالي ←", callback_data=f"quran_p{page+1}"))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton("🎧 استمع لسورة", callback_data="listen_menu")])
    buttons.append([InlineKeyboardButton("رجوع للقائمة", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)

RECITERS = {
    "ayoub":  ("محمد أيوب",          "https://server16.mp3quran.net/ayyoub2/Rewayat-Hafs-A-n-Assem/"),
    "shur":   ("سعود الشريم",        "https://server7.mp3quran.net/shur/"),
    "arkani": ("عبدالولي الأركاني",  "https://server6.mp3quran.net/arkani/"),
    "a_jbr":  ("علي جابر",           "https://server11.mp3quran.net/a_jbr/"),
    "sds":    ("عبدالرحمن السديس",   "https://server11.mp3quran.net/sds/"),
    "maher":  ("ماهر المعيقلي",      "https://server12.mp3quran.net/maher/"),
}

def reciter_keyboard():
    rows = []
    keys = list(RECITERS.keys())
    for i in range(0, len(keys), 2):
        row = []
        for key in keys[i:i+2]:
            name, _ = RECITERS[key]
            row.append(InlineKeyboardButton(f"🎤 {name}", callback_data=f"listen_{key}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("رجوع للقائمة", callback_data="menu")])
    return InlineKeyboardMarkup(rows)

def listen_surah_keyboard(reciter_key, page=0):
    per_page = 18
    total_pages = (len(QURAN_SURAHS) + per_page - 1) // per_page
    start = page * per_page
    end = min(start + per_page, len(QURAN_SURAHS))
    buttons = []
    for i in range(start, end, 3):
        row = []
        for j in range(i, min(i + 3, end)):
            num = j + 1
            name = QURAN_SURAHS[j]
            row.append(InlineKeyboardButton(f"{num}. {name}", callback_data=f"laudio_{reciter_key}_{num}"))
        buttons.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("→ السابق", callback_data=f"lp_{reciter_key}_{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("التالي ←", callback_data=f"lp_{reciter_key}_{page+1}"))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton("← القرّاء", callback_data="listen_menu")])
    buttons.append([InlineKeyboardButton("رجوع للقائمة", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)

ATHAR_SURAHS_PER_PAGE = 9
ATHAR_RECITERS = [
    ("محمد أيوب",         "https://server16.mp3quran.net/ayyoub2/Rewayat-Hafs-A-n-Assem/"),
    ("سعود الشريم",       "https://server7.mp3quran.net/shur/"),
    ("عبدالولي الأركاني", "https://server6.mp3quran.net/arkani/"),
    ("علي جابر",          "https://server11.mp3quran.net/a_jbr/"),
    ("عبدالرحمن السديس",  "https://server11.mp3quran.net/sds/"),
    ("ماهر المعيقلي",     "https://server12.mp3quran.net/maher/"),
]

def athar_surah_page_rows(page):
    per   = ATHAR_SURAHS_PER_PAGE
    start = page * per
    end   = min(start + per, len(QURAN_SURAHS))
    total = (len(QURAN_SURAHS) - 1) // per + 1
    rows  = []
    for i in range(start, end, 3):
        rows.append([QURAN_SURAHS[j] for j in range(i, min(i + 3, end))])
    nav = []
    if page > 0:     nav.append("◀️ السابق")
    nav.append(f"📄 {page+1}/{total}")
    if end < len(QURAN_SURAHS): nav.append("▶️ التالي")
    rows.append(nav)
    rows.append(["🔙 القائمة الرئيسية"])
    return rows, page, total

async def show_athar_quran_page(update, context, page):
    rows, p, total = athar_surah_page_rows(page)
    context.user_data["athar_quran_page"] = p
    kb = ReplyKeyboardMarkup(rows, resize_keyboard=True)
    msg = update.effective_message
    await msg.reply_text(
        f"📖 القرآن الكريم 🤍\n\nاختر سورة — الصفحة {p+1}/{total}:",
        reply_markup=kb,
    )

def athar_surah_detail_kb(surah_num):
    n = str(surah_num).zfill(3)
    buttons = [
        [InlineKeyboardButton("📖 اقرأ السورة — quran.com", url=f"https://quran.com/ar/{surah_num}")],
        [
            InlineKeyboardButton("🎧 محمد أيوب",    url=f"https://server16.mp3quran.net/ayyoub2/Rewayat-Hafs-A-n-Assem/{n}.mp3"),
            InlineKeyboardButton("🎧 سعود الشريم",  url=f"https://server7.mp3quran.net/shur/{n}.mp3"),
        ],
        [
            InlineKeyboardButton("🎧 الأركاني",     url=f"https://server6.mp3quran.net/arkani/{n}.mp3"),
            InlineKeyboardButton("🎧 علي جابر",     url=f"https://server11.mp3quran.net/a_jbr/{n}.mp3"),
        ],
        [
            InlineKeyboardButton("🎧 السديس",       url=f"https://server11.mp3quran.net/sds/{n}.mp3"),
            InlineKeyboardButton("🎧 ماهر المعيقلي", url=f"https://server12.mp3quran.net/maher/{n}.mp3"),
        ],
        [InlineKeyboardButton("🔙 رجوع للسور", callback_data="athar_back_surahs")],
    ]
    return InlineKeyboardMarkup(buttons)

SEPARATOR_LINE = "═══ • ═══ ✨ ═══ • ═══"

def get_separator():
    now = datetime.datetime.now(TIMEZONE)
    hijri = Gregorian(now.year, now.month, now.day).to_hijri()
    h_text = f"{hijri.day} {HIJRI_MONTHS[hijri.month]} {hijri.year} هـ"
    g_text = f"{now.day} {GREGORIAN_MONTHS[now.month]} {now.year} م"
    day_name = DAYS_AR.get(now.weekday(), "")
    time_text = now.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
    return f"{h_text} — {day_name}\n{SEPARATOR_LINE}\n{g_text} — {time_text}"

def footer_msg():
    return f"""لا تنسون تدعون لـ محمد صابر روزي وعائشه ملا ولجميع اموات المسلمين بالرحمة والمغفرة.. اللهم اجعل نورهما لا ينطفئ واجمعنا بهم في جنات النعيم 🤍

{get_date_line()}"""


async def send_to_channel(bot: Bot, text: str, image_filename: str = None, parse_mode: str = None, send_separator: bool = False):
    if not CHANNEL_ID:
        return
    full_text = f"{text}\n\n{get_date_line()}"
    try:
        await bot.send_message(
            chat_id=CHANNEL_ID, text=full_text,
            parse_mode=parse_mode, disable_web_page_preview=True
        )
        if send_separator:
            await bot.send_message(chat_id=CHANNEL_ID, text=get_separator())
    except TelegramError as e:
        logger.error(f"Failed to send to channel: {e}")


async def job_morning_azkar(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, MORNING_AZKAR_TEXT, send_separator=True)

async def job_evening_azkar(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, EVENING_AZKAR_TEXT, send_separator=True)

async def job_sleep_azkar(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, SLEEP_AZKAR_TEXT, send_separator=True)

async def job_salawat(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, SALAWAT_TEXT, send_separator=True)

async def job_istijaba(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, ISTIJABA_TEXT, send_separator=True)

async def job_social(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, SOCIAL_TEXT, parse_mode="HTML", send_separator=True)

async def job_kahf(context: ContextTypes.DEFAULT_TYPE):
    await send_to_channel(context.bot, KAHF_TEXT, parse_mode="HTML", send_separator=True)

async def job_prayer_alert(context: ContextTypes.DEFAULT_TYPE):
    prayer_key = context.job.data
    text = get_single_prayer_text(prayer_key)
    await send_to_channel(context.bot, text, send_separator=True)

async def job_schedule_prayer_alerts(context: ContextTypes.DEFAULT_TYPE):
    import datetime as dt
    makkah_times = fetch_prayer_times("Makkah")
    if not makkah_times:
        return
    now = datetime.datetime.now(TIMEZONE)
    for old_job in context.job_queue.get_jobs_by_name("prayer_alert"):
        old_job.schedule_removal()
    for prayer_key in PRAYER_NAMES_ORDER:
        time_str = makkah_times.get(prayer_key)
        if not time_str:
            continue
        hour, minute = map(int, time_str.split(":"))
        prayer_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if prayer_dt > now:
            delay = (prayer_dt - now).total_seconds()
            context.job_queue.run_once(job_prayer_alert, when=delay, data=prayer_key, name="prayer_alert")

async def job_daily_story(context: ContextTypes.DEFAULT_TYPE):
    import random
    funcs = [get_random_nabiy, get_random_sahabi, get_random_quran_story]
    story = random.choice(funcs)()
    await send_to_channel(context.bot, story, send_separator=True)

async def job_daily_quiz(context: ContextTypes.DEFAULT_TYPE):
    quiz = get_random_quiz()
    try:
        question_text = f"سؤال اليوم 🤍\n\n{quiz['q']}"
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


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key = "✅ موجود" if OPENROUTER_API_KEY else "❌ غير موجود"
    await update.message.reply_text(f"🏓 البوت يعمل!\nOPENROUTER_API_KEY: {key}")

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)
    combined = (
        WELCOME_TEXT
        + "\n\n━━━━━━━━━━━━━━\n"
        "📋 *اختر ما تريد:*\nأو اكتب سؤالك الديني مباشرة وسأجيبك 🤍"
    )
    await update.message.reply_text(combined, parse_mode="Markdown", reply_markup=main_inline_menu())

async def cmd_athar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 *اختر ما تريد:*\nأو اكتب سؤالك الديني مباشرة وسأجيبك 🤍", parse_mode="Markdown", reply_markup=main_inline_menu())

async def cmd_testai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    key_set = bool(OPENROUTER_API_KEY)
    key_preview = f"{OPENROUTER_API_KEY[:8]}..." if key_set else "---"
    if not key_set:
        await update.message.reply_text("❌ OPENROUTER_API_KEY غير موجود في Render.")
        return
    await update.message.reply_chat_action("typing")
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "أنت مساعد إسلامي"},
            {"role": "user", "content": "ما هي أركان الإسلام الخمسة؟"},
        ],
        "max_tokens": 200,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_URL,
                json=payload,
                headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                data = await resp.json()
                if "choices" in data:
                    text = data["choices"][0]["message"]["content"]
                    await update.message.reply_text(f"✅ الذكاء الاصطناعي يعمل:\n\n{text[:300]}")
                else:
                    err = data.get("error", {})
                    await update.message.reply_text(
                        f"❌ خطأ:\nكود: {err.get('code')}\n{err.get('message','؟')}\n"
                        f"المفتاح يبدأ بـ: {key_preview}"
                    )
    except Exception as e:
        await update.message.reply_text(f"❌ استثناء: {e}")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    handlers = {
        "dua": get_random_dua,
        "dua_nabi": get_random_dua_nabi,
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
        await query.message.reply_text("📋 *اختر ما تريد:*\nأو اكتب سؤالك الديني مباشرة وسأجيبك 🤍", parse_mode="Markdown", reply_markup=main_inline_menu())
        return
    elif data == "azkar_daily":
        await query.message.reply_text("الاذكار اليومية 🤍\n\nاختر:", reply_markup=azkar_daily_keyboard())
    elif data in ("sabah", "masa", "nawm"):
        funcs = {"sabah": get_random_azkar_sabah, "masa": get_random_azkar_masa, "nawm": get_random_azkar_nawm}
        text = funcs[data]()
        await query.message.reply_text(text)
        await query.message.reply_text(get_separator())
        await query.message.reply_text(footer_msg(), reply_markup=azkar_daily_keyboard())
        return
    elif data == "quran_menu":
        await show_athar_quran_page(update, context, 0)
    elif data.startswith("quran_p"):
        page = int(data[7:])
        await show_athar_quran_page(update, context, page)
    elif data == "athar_back_surahs":
        page = context.user_data.get("athar_quran_page", 0)
        await show_athar_quran_page(update, context, page)
    elif data == "listen_menu":
        await query.message.reply_text("🎧 اختر القارئ:", reply_markup=reciter_keyboard())
    elif data.startswith("listen_") and not data.startswith("listen_menu"):
        key = data[7:]
        if key in RECITERS:
            name, _ = RECITERS[key]
            await query.message.reply_text(f"🎤 {name}\n\nاختر السورة:", reply_markup=listen_surah_keyboard(key, 0))
    elif data.startswith("lp_"):
        parts = data[3:].rsplit("_", 1)
        if len(parts) == 2:
            key, page = parts[0], int(parts[1])
            if key in RECITERS:
                name, _ = RECITERS[key]
                await query.message.reply_text(f"🎤 {name}\n\nاختر السورة:", reply_markup=listen_surah_keyboard(key, page))
    elif data.startswith("laudio_"):
        parts = data[7:].rsplit("_", 1)
        if len(parts) == 2:
            key, num = parts[0], int(parts[1])
            if key in RECITERS and 1 <= num <= 114:
                r_name, base_url = RECITERS[key]
                s_name = QURAN_SURAHS[num - 1]
                url = f"{base_url}{num:03d}.mp3"
                await query.message.reply_text(
                    f"🎧 سورة {s_name} — {r_name}\n\n{url}",
                    disable_web_page_preview=True
                )
    elif data == "asma":
        await query.message.reply_text("اسماء الله الحسنى 🤍\n\nاختر اسما لمعرفة معناه:", reply_markup=asma_keyboard(0))
    elif data.startswith("asma_p"):
        page = int(data[6:])
        await query.message.reply_text("اسماء الله الحسنى 🤍\n\nاختر اسما لمعرفة معناه:", reply_markup=asma_keyboard(page))
    elif data.startswith("asma_") and not data.startswith("asma_p"):
        idx = int(data[5:])
        if 0 <= idx < len(ALLAH_NAMES):
            entry = ALLAH_NAMES[idx]
            page = idx // NAMES_PER_PAGE
            text = f"{idx+1}. {entry['name']} 🤍\n\n{entry['meaning']}"
            await query.message.reply_text(text)
            await query.message.reply_text(get_separator())
            await query.message.reply_text(footer_msg(), reply_markup=asma_keyboard(page))
        return
    elif data == "noop":
        return
    elif data in ("prophets_menu", "prophets_page1"):
        await query.message.reply_text("السيرة النبوية 🤍\n\nاختر نبيا لقراءة سيرته:", reply_markup=prophets_keyboard_page1())
    elif data == "prophets_page2":
        await query.message.reply_text("السيرة النبوية 🤍\n\nاختر نبيا لقراءة سيرته:", reply_markup=prophets_keyboard_page2())
    elif data.startswith("prophet_") and not data.startswith("prophet_info_") and data[8:] in PROPHETS:
        prophet_key = data[8:]
        prophet = PROPHETS[prophet_key]
        page1_keys = list(PROPHETS.keys())[:12]
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("سيرته", callback_data=f"prophet_info_{prophet_key}_story")],
            [InlineKeyboardButton("زوجاته", callback_data=f"prophet_info_{prophet_key}_wives")],
            [InlineKeyboardButton("أولاده", callback_data=f"prophet_info_{prophet_key}_children")],
            [InlineKeyboardButton("رجوع للأنبياء", callback_data="prophets_page1" if prophet_key in page1_keys else "prophets_page2")],
            [InlineKeyboardButton("رجوع للقائمة", callback_data="menu")],
        ])
        await query.message.reply_text(f"{prophet['name']} 🤍\n\nاختر ما تريد معرفته:", reply_markup=keyboard)
    elif data.startswith("prophet_info_"):
        parts = data[len("prophet_info_"):].rsplit("_", 1)
        prophet_key = parts[0]
        info_type = parts[1]
        if prophet_key in PROPHETS and info_type in ("story", "wives", "children"):
            prophet = PROPHETS[prophet_key]
            text = prophet.get(info_type, "لا توجد معلومات متوفرة")
            await query.message.reply_text(text)
            await query.message.reply_text(get_separator())
            page1_keys = list(PROPHETS.keys())[:12]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("سيرته", callback_data=f"prophet_info_{prophet_key}_story")],
                [InlineKeyboardButton("زوجاته", callback_data=f"prophet_info_{prophet_key}_wives")],
                [InlineKeyboardButton("أولاده", callback_data=f"prophet_info_{prophet_key}_children")],
                [InlineKeyboardButton("رجوع للأنبياء", callback_data="prophets_page1" if prophet_key in page1_keys else "prophets_page2")],
                [InlineKeyboardButton("رجوع للقائمة", callback_data="menu")],
            ])
            await query.message.reply_text(footer_msg(), reply_markup=keyboard)
    elif data == "prayer_times":
        await query.message.reply_text("اوقات الصلاة 🤍\n\nاختر المناطق او المدن:", reply_markup=prayer_times_keyboard())
    elif data == "pt_regions":
        await query.message.reply_text("اختر المنطقة 🤍", reply_markup=regions_keyboard())
    elif data == "pt_cities":
        await query.message.reply_text("اختر المدينة 🤍", reply_markup=cities_keyboard())
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
        await query.message.reply_text("📋 *اختر ما تريد:*\nأو اكتب سؤالك الديني مباشرة وسأجيبك 🤍", parse_mode="Markdown", reply_markup=main_inline_menu())


def _strip(text):
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


SPECIAL_VERSES = {
    "آية الكرسي": "KURSI",
    "اية الكرسي": "KURSI",
    "خواتيم البقرة": "KHAWATIM",
    "خواتيم سورة البقرة": "KHAWATIM",
    "خواتيم البقره": "KHAWATIM",
}

ADMIN_IDS = []

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    msg = update.message.text.strip()
    clean = _strip(msg)

    if msg in _FULL_ANSWER_TRIGGERS:
        last_q = context.user_data.get("last_ai_q")
        if last_q and OPENROUTER_API_KEY:
            await update.message.reply_chat_action("typing")
            full_ans = await ask_gemini(last_q, full=True)
            if full_ans:
                await update.message.reply_text(
                    f"🤖 *الجواب الكامل:*\n\n{full_ans}\n\n"
                    "━━━━━━━━━━━━━━\n"
                    "⚠️ _للأمور الفقهية الشخصية، راجع عالماً متخصصاً_",
                    parse_mode="Markdown",
                )
                return
        await update.message.reply_text("لا يوجد سؤال سابق، اكتب سؤالك أولاً 🤍")
        return

    links_in_msg = msg.strip().split()
    tiktok_links = [l for l in links_in_msg if "tiktok.com" in l]
    insta_links = [l for l in links_in_msg if "instagram.com" in l]
    all_social_links = tiktok_links + insta_links

    if all_social_links and CHANNEL_ID:
        user_id = update.message.from_user.id if update.message.from_user else None
        if not ADMIN_IDS or (user_id and user_id in ADMIN_IDS):
            if tiktok_links and insta_links:
                platform = "الانستقرام والتيك توك"
            elif tiktok_links:
                platform = "تيك توك"
            else:
                platform = "انستقرام"
            link_parts = []
            for l in all_social_links:
                if "tiktok" in l:
                    link_parts.append(f'<a href="{l}">تيك توك</a>')
                else:
                    link_parts.append(f'<a href="{l}">انستقرام</a>')
            links_text = " — ".join(link_parts)
            caption = f"""مقطع جديد على {platform} 🤍

لا تنسون تدعون لـ محمد صابر روزي وعائشه ملا ولجميع اموات المسلمين 🤍

{links_text}

{get_date_line()}"""
            wait_msg = await update.message.reply_text("جاري نشر الرابط... 🤍")
            try:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID, text=caption,
                    parse_mode="HTML", disable_web_page_preview=False
                )
                await wait_msg.edit_text("تم نشر الرابط في القناة 🤍")
            except TelegramError as te:
                await wait_msg.edit_text(f"ما قدرت انشر: {te}")
            return

    if msg in ("اوقات الصلاة", "أوقات الصلاة", "الصلاة", "مواقيت الصلاة"):
        text = get_prayer_times_text()
        await update.message.reply_text(text)
        await update.message.reply_text(get_separator())
        await update.message.reply_text(footer_msg(), reply_markup=back_keyboard())
        return

    if msg in ("اثر", "أثر", "القائمة", "المساعدة", "🔙 القائمة الرئيسية", "📋 القائمة"):
        await update.message.reply_text("📋 *اختر ما تريد:*\nأو اكتب سؤالك الديني مباشرة وسأجيبك 🤍", parse_mode="Markdown", reply_markup=main_inline_menu())
        return

    # ══ أزرار القائمة الرئيسية ══
    async def _send(func):
        text = func()
        await update.message.reply_text(text)
        await update.message.reply_text(get_separator())
        await update.message.reply_text(footer_msg(), reply_markup=back_keyboard())

    if msg == "📖 القرآن الكريم":
        await show_athar_quran_page(update, context, 0)
        return
    if msg == "🌿 الاذكار اليومية":
        await update.message.reply_text("الاذكار اليومية 🤍\n\nاختر:", reply_markup=azkar_daily_keyboard())
        return
    if msg == "🤲 دعاء":
        await _send(get_random_dua); return
    if msg == "🕊️ ادعية الانبياء":
        await _send(get_random_dua_nabi); return
    if msg == "✨ آية قرآنية":
        await _send(get_random_ayah); return
    if msg == "🌙 السيرة النبوية":
        await update.message.reply_text("السيرة النبوية 🤍\n\nاختر نبيا لقراءة سيرته:", reply_markup=prophets_keyboard_page1())
        return
    if msg == "⭐ قصة صحابي":
        await _send(get_random_sahabi); return
    if msg == "📜 قصة قرآنية":
        await _send(get_random_quran_story); return
    if msg == "💎 الباقيات الصالحات":
        await update.message.reply_text(BAQIYAT)
        await update.message.reply_text(get_separator())
        await update.message.reply_text(footer_msg(), reply_markup=back_keyboard())
        return
    if msg == "🛡️ تحصين النفس":
        await _send(get_random_tahseen); return
    if msg == "🔵 آية الكرسي":
        await update.message.reply_text(AYAT_KURSI)
        await update.message.reply_text(get_separator())
        await update.message.reply_text(footer_msg(), reply_markup=back_keyboard())
        return
    if msg == "📚 حديث نبوي":
        await _send(get_random_hadith); return
    if msg == "🌟 اسماء الله الحسنى":
        await update.message.reply_text("اسماء الله الحسنى 🤍\n\nاختر اسما لمعرفة معناه:", reply_markup=asma_keyboard(0))
        return
    if msg == "🌸 فضائل الاعمال":
        await _send(get_random_fadl); return
    if msg == "🕌 اذكار بعد الصلاة":
        await _send(get_random_azkar_salah); return
    if msg == "💫 الاستغفار":
        await _send(get_random_istighfar); return
    if msg == "🌺 آداب اسلامية":
        await _send(get_random_adab); return
    if msg == "🕐 اوقات الصلاة":
        await update.message.reply_text("اوقات الصلاة 🤍\n\nاختر:", reply_markup=prayer_times_keyboard())
        return
    if msg == "🌐 الموقع الرسمي":
        await update.message.reply_text("🌐 الموقع الرسمي:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("فتح الموقع", url="https://legendary-yeot-b80ee7.netlify.app/")]]))
        return
    if msg == "📢 قناة اثر":
        await update.message.reply_text("📢 قناة اثر:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("فتح القناة", url="https://t.me/Athar_Atkar")]]))
        return
    if msg == "📸 انستقرام":
        await update.message.reply_text("📸 انستقرام:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("فتح الصفحة", url="https://www.instagram.com/1947_1951?igsh=bnA3cXloanFvazJx&utm_source=qr")]]))
        return
    if msg == "🎬 تيك توك":
        await update.message.reply_text("🎬 تيك توك:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("فتح الصفحة", url="https://www.tiktok.com/@1947_1951?_r=1&_t=ZS-94zjaTgMqE4")]]))
        return

    # اسم السورة يشتغل دائماً بصرف النظر عن الـ state
    surah_num_match = next((i + 1 for i, n in enumerate(QURAN_SURAHS) if n == msg), None)
    if surah_num_match:
        text = (
            f"📖 *سورة {msg}*\n"
            f"🔢 رقمها: *{surah_num_match}*\n\n"
            f"اختر القراءة أو الاستماع:"
        )
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=athar_surah_detail_kb(surah_num_match),
        )
        return

    if "athar_quran_page" in context.user_data:
        page = context.user_data["athar_quran_page"]
        if msg == "▶️ التالي":
            await show_athar_quran_page(update, context, page + 1)
            return
        elif msg == "◀️ السابق":
            await show_athar_quran_page(update, context, max(0, page - 1))
            return
        elif msg.startswith("📄 "):
            return

    simple_map = {
        ("اذكار", "أذكار", "ذكر"): get_random_azkar,
        ("اذكار الصباح", "أذكار الصباح", "صباح"): get_random_azkar_sabah,
        ("اذكار المساء", "أذكار المساء", "مساء"): get_random_azkar_masa,
        ("اذكار النوم", "أذكار النوم", "نوم"): get_random_azkar_nawm,
        ("دعاء", "ادعية", "أدعية", "دعوة"): get_random_dua,
        ("قصة", "قصص", "انبياء", "أنبياء", "نبي"): get_random_nabiy,
        ("آية", "اية", "قرآن", "قران"): get_random_ayah,
        ("صحابة", "صحابي", "صحابه"): get_random_sahabi,
        ("قصة قرآنية", "قصص القرآن", "قصه قرآنيه"): get_random_quran_story,
        ("ادعية الانبياء", "دعاء الانبياء", "دعاء نبي"): get_random_dua_nabi,
        ("تحصين", "تحصين النفس", "تحصن"): get_random_tahseen,
        ("حديث", "احاديث", "حديث نبوي"): get_random_hadith,
        ("اسماء الله", "اسماء الله الحسنى", "أسماء الله"): get_random_asma,
        ("فضائل", "فضائل الاعمال", "فضل"): get_random_fadl,
        ("اذكار الصلاة", "اذكار بعد الصلاة", "بعد الصلاة"): get_random_azkar_salah,
        ("استغفار", "استغفر", "الاستغفار"): get_random_istighfar,
        ("آداب", "اداب", "آداب اسلامية"): get_random_adab,
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

    if OPENROUTER_API_KEY and len(msg.strip()) >= 5:
        wait_msg = await update.message.reply_text("⏳ جاري التفكير...")
        answer = await ask_gemini(msg, full=False)
        await wait_msg.delete()
        if answer:
            context.user_data["last_ai_q"] = msg
            await update.message.reply_text(
                f"🤖 *جواب مختصر:*\n\n{answer}\n\n"
                "━━━━━━━━━━━━━━\n"
                "📝 _للجواب الكامل اكتب:_ *الجواب كامل*",
                parse_mode="Markdown",
            )
            return
        await update.message.reply_text(
            "⚠️ لم أستطع الإجابة الآن، حاول مرة أخرى بعد لحظات 🙏"
        )
        return


async def _delete_msgs(context: ContextTypes.DEFAULT_TYPE, chat_id, msg_id1, msg_id2):
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id1)
        await context.bot.delete_message(chat_id=chat_id, message_id=msg_id2)
    except TelegramError as e:
        logger.warning(f"Could not delete messages: {e}")


def channel_welcome():
    return f"""نورتنا بين اهلك وناسك 🤍

هنا مكانك ومحطتك للهدوء وطمأنينة القلب

وجودك معنا مو مجرد رقم هو "اثر" طيب يجمعنا على ذكر الله وقصص الخير

صدقة جارية عن محمد صابر روزي وعائشه ملا ولجميع اموات المسلمين 🫶🏻

{get_date_line()}"""


async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.chat_member or not CHANNEL_ID:
        return
    member = update.chat_member
    if member.new_chat_member.status in ("member", "creator", "administrator"):
        if member.old_chat_member.status in ("left", "kicked"):
            user = member.new_chat_member.user
            try:
                welcome_msg = await context.bot.send_message(
                    chat_id=CHANNEL_ID, text=channel_welcome()
                )
                social_msg = await context.bot.send_message(
                    chat_id=CHANNEL_ID, text=SOCIAL_TEXT,
                    parse_mode="HTML", disable_web_page_preview=True
                )
                context.job_queue.run_once(
                    lambda ctx, cid=CHANNEL_ID, mid1=welcome_msg.message_id, mid2=social_msg.message_id: _delete_msgs(ctx, cid, mid1, mid2),
                    when=120,
                    name=f"delete_welcome_{user.id}"
                )
            except TelegramError as e:
                logger.warning(f"Could not send channel welcome: {e}")


def build_application() -> Application:
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is not set!")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_athar))
    app.add_handler(CommandHandler("athar",  cmd_athar))
    app.add_handler(CommandHandler("users",  cmd_users))
    app.add_handler(CommandHandler("ping",   cmd_ping))
    app.add_handler(CommandHandler("testai", cmd_testai))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(ChatMemberHandler(handle_new_member, ChatMemberHandler.CHAT_MEMBER))

    jq = app.job_queue

    jq.run_daily(job_morning_azkar, time=datetime.time(5, 15, tzinfo=TIMEZONE), name="اذكار الصباح")
    jq.run_daily(job_evening_azkar, time=datetime.time(18, 30, tzinfo=TIMEZONE), name="اذكار المساء")
    jq.run_daily(job_sleep_azkar,   time=datetime.time(21, 30, tzinfo=TIMEZONE), name="اذكار النوم")
    jq.run_daily(job_salawat,   time=datetime.time(8, 30, tzinfo=TIMEZONE), days=(4,), name="الصلاة على النبي")
    jq.run_daily(job_kahf,      time=datetime.time(8, 30, tzinfo=TIMEZONE), days=(4,), name="سورة الكهف")
    jq.run_daily(job_istijaba,  time=datetime.time(16, 30, tzinfo=TIMEZONE), days=(4,), name="ساعة الاستجابة")
    jq.run_daily(job_social,    time=datetime.time(20, 0, tzinfo=TIMEZONE),  days=(4,), name="حسابات التواصل")
    jq.run_daily(job_schedule_prayer_alerts, time=datetime.time(1, 0, tzinfo=TIMEZONE), name="جدولة تنبيهات الصلاة")
    jq.run_once(job_schedule_prayer_alerts, when=5, name="جدولة تنبيهات الصلاة الآن")
    jq.run_daily(job_daily_story, time=datetime.time(16, 0, tzinfo=TIMEZONE), name="قصة يومية")
    jq.run_daily(job_daily_quiz,  time=datetime.time(14, 0, tzinfo=TIMEZONE), name="سؤال يومي")

    logger.info("Application built with all handlers and scheduled jobs.")
    return app


if __name__ == "__main__":
    application = build_application()
    print("البوت بدأ العمل الآن... 🚀")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
