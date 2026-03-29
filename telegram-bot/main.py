import os
import json
import logging
import random
import asyncio
import threading
import aiohttp
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import pytz
from hijridate import Gregorian

from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)
from telegram.constants import ParseMode

from names_of_allah import NAMES_OF_ALLAH
from prophets import PROPHETS
from quran_data import SURAHS, AZKAR, HADITH_OF_DAY
from prayer_data import COUNTRIES, SA_REGIONS, PRAYER_METHODS
from islamic_content import (
    DUAS, SAHABA, QURAN_STORIES, FADHAIL,
    ADAB, TAHSIN, BAQIYAT, ISTIGHFAR, AYAT_KARIMA,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

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
            "joined": datetime.now(pytz.timezone("Asia/Riyadh")).strftime("%Y-%m-%d %H:%M"),
        }
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass

async def cmd_users(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    users = load_users()
    count = len(users)
    if count == 0:
        await update.message.reply_text("لا يوجد مستخدمون بعد.")
        return
    lines = [f"👥 المستخدمون في بوت الأذكار: {count}\n"]
    for u in users.values():
        lines.append(f"• {u['name']} {u['username']}\n  انضم: {u['joined']}")
    await update.message.reply_text("\n".join(lines))

logger = logging.getLogger(__name__)

TOKEN = os.getenv("AZKAR_BOT_TOKEN")


# ─── الأشهر والأيام بالعربي ────────────────────────────
_MONTHS_AR  = ["يناير","فبراير","مارس","أبريل","مايو","يونيو",
                "يوليو","أغسطس","سبتمبر","أكتوبر","نوفمبر","ديسمبر"]
_HIJRI_AR   = ["محرم","صفر","ربيع الأول","ربيع الآخر","جمادى الأولى",
                "جمادى الآخرة","رجب","شعبان","رمضان","شوال","ذو القعدة","ذو الحجة"]
_DAYS_AR    = ["الاثنين","الثلاثاء","الأربعاء","الخميس","الجمعة","السبت","الأحد"]
_TZ         = pytz.timezone("Asia/Riyadh")

def get_footer() -> str:
    """يولّد فاصلة تحوي التاريخ والوقت."""
    now      = datetime.now(_TZ)
    hijri    = Gregorian(now.year, now.month, now.day).to_hijri()
    greg_str = f"{now.day} {_MONTHS_AR[now.month-1]} {now.year} م"
    hij_str  = f"{hijri.day} {_HIJRI_AR[hijri.month-1]} {hijri.year} هـ"
    day_ar   = _DAYS_AR[now.weekday()]
    hour     = now.strftime("%I:%M")
    period   = "ص" if now.hour < 12 else "م"
    return (
        f"\n\n{hij_str} — {day_ar}\n"
        "═══ • ═══ ✨ ═══ • ═══\n"
        f"{greg_str} — {hour} {period}"
    )

# ─── دعاء يُرسل مع كل رسالة ────────────────────────────
DUA_GHAZI = (
    "🤍 اللهم اجعل هذا العمل صدقة جارية في ميزان حسنات السيد غازي عجاج، "
    "ونوراً له في قبره لا ينطفئ.. نسألكم الدعاء له بالرحمة والمغفرة، "
    "وأن يسكنه الله فسيح جناته."
)

# ─── helper ────────────────────────────────────────────
def kb(rows, resize=True):
    return ReplyKeyboardMarkup(rows, resize_keyboard=resize)

def state(ctx):
    return ctx.user_data.get("s", "main")

def set_state(ctx, s, **extra):
    ctx.user_data["s"] = s
    ctx.user_data.update(extra)

async def reply(update, text, markup=None, md=True):
    """أرسل الرسالة + التذييل، ثم دعاء غازي عجاج في رسالة منفصلة."""
    full = text + get_footer()
    await update.effective_message.reply_text(
        full,
        parse_mode=ParseMode.MARKDOWN if md else None,
        reply_markup=markup,
    )
    await update.effective_message.reply_text(DUA_GHAZI)

# ─── KEYBOARDS ─────────────────────────────────────────

MAIN_KB = kb([["📋 القائمة"]])

BACK_MAIN = "📋 القائمة"


def main_inline_menu_ghazi():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 القرآن الكريم", callback_data="gmenu_quran")],
        [InlineKeyboardButton("🌅 الاذكار اليومية", callback_data="gmenu_azkar"),
         InlineKeyboardButton("🤲 دعاء", callback_data="gmenu_dua")],
        [InlineKeyboardButton("🌟 آية قرآنية", callback_data="gmenu_aya"),
         InlineKeyboardButton("🕌 ادعية الانبياء", callback_data="gmenu_prophets")],
        [InlineKeyboardButton("📚 قصة صحابي", callback_data="gmenu_sahaba"),
         InlineKeyboardButton("🌙 السيرة النبوية", callback_data="gmenu_seerah")],
        [InlineKeyboardButton("💎 الباقيات الصالحات", callback_data="gmenu_baqiyat"),
         InlineKeyboardButton("📜 قصة قرآنية", callback_data="gmenu_qstories")],
        [InlineKeyboardButton("🛡️ آية الكرسي", callback_data="gmenu_kursi"),
         InlineKeyboardButton("🔰 تحصين النفس", callback_data="gmenu_tahsin")],
        [InlineKeyboardButton("📿 اسماء الله الحسنى", callback_data="gmenu_asma"),
         InlineKeyboardButton("📝 حديث نبوي", callback_data="gmenu_hadith")],
        [InlineKeyboardButton("🕌 اذكار بعد الصلاة", callback_data="gmenu_azkar_salah"),
         InlineKeyboardButton("⭐ فضائل الاعمال", callback_data="gmenu_fadhail")],
        [InlineKeyboardButton("🌺 آداب اسلامية", callback_data="gmenu_adab"),
         InlineKeyboardButton("🙏 الاستغفار", callback_data="gmenu_istighfar")],
        [InlineKeyboardButton("🕐 اوقات الصلاة", callback_data="gmenu_prayer")],
        [InlineKeyboardButton("🎙️ صوتيه تكبيرات للسيد غازي", callback_data="gmenu_takbeer")],
    ])

# ─── WELCOME ───────────────────────────────────────────

WELCOME = (
    "🌙 *أهلاً بك في بوت الأذكار* 🌙\n\n"
    "🤍 *اللهم اجعل هذا البوت صدقة جارية في ميزان حسنات*\n"
    "*السيد غازي عجاج رحمه الله،*\n"
    "*ونوراً له لا ينطفئ، وارفع درجاته في الفردوس الأعلى* 🤍\n\n"
    "اختر ما تريد من الأزرار بالأسفل ♡"
)

async def show_main(update, context, text=None):
    set_state(context, "main")
    combined = (
        (text or WELCOME)
        + "\n\n━━━━━━━━━━━━━━\n"
        "📋 *اختر ما تريد:*"
    )
    await update.effective_message.reply_text(combined, parse_mode=ParseMode.MARKDOWN, reply_markup=main_inline_menu_ghazi())

# ─── START ─────────────────────────────────────────────

async def cmd_start(update, context):
    save_user(update.effective_user)
    await show_main(update, context)

async def cmd_ping(update, context):
    await update.message.reply_text("🏓 البوت يعمل!")

# ─── MESSAGE ROUTER ─────────────────────────────────────

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    s   = state(context)

    if txt in (BACK_MAIN, "📋 القائمة", "🔙 القائمة الرئيسية"):
        await show_main(update, context)
        return

    # اسم السورة يشتغل بصرف النظر عن الـ state
    surah_match = next((x for x in SURAHS if f"{x['number']}. {x['name']}" == txt), None)
    if surah_match:
        page = context.user_data.get("ghazi_quran_page", 0)
        context.user_data["ghazi_quran_page"] = page
        text = (
            f"📖 *سورة {surah_match['name']}*\n"
            f"🔢 رقمها: *{surah_match['number']}* | "
            f"📝 آياتها: *{surah_match['verses']}* آية | "
            f"🕌 *{surah_match['type']}*\n\n"
            f"اضغط الزر أدناه لقراءة السورة أو الاستماع:"
        )
        await update.effective_message.reply_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=ghazi_surah_keyboard(surah_match['number']),
        )
        return

    if s == "main":
        await route_main(update, context, txt)
    elif s == "quran":
        await route_quran(update, context, txt)
    elif s.startswith("quran_surahs"):
        await route_surah_page(update, context, txt, s)
    elif s == "azkar":
        await route_azkar_section(update, context, txt)
    elif s == "prophets":
        await route_prophet_list(update, context, txt)
    elif s == "prophet_menu":
        await route_prophet_menu(update, context, txt)
    elif s == "seerah":
        await route_seerah(update, context, txt)
    elif s == "sahaba":
        await route_sahaba(update, context, txt)
    elif s == "quran_stories":
        await route_quran_story(update, context, txt)
    elif s == "tahsin":
        await route_tahsin(update, context, txt)
    elif s.startswith("asma"):
        await route_asma(update, context, txt, s)
    elif s == "fadhail":
        await route_fadhail(update, context, txt)
    elif s == "adab":
        await route_adab(update, context, txt)
    elif s == "istighfar":
        await route_istighfar(update, context, txt)
    elif s == "prayer_countries":
        await route_prayer_country(update, context, txt)
    elif s == "prayer_regions":
        await route_prayer_region(update, context, txt)
    elif s == "prayer_cities":
        await route_prayer_city(update, context, txt)
    else:
        # fallback: إذا كان النص اسم سورة بصرف النظر عن الـ state
        surah = next((x for x in SURAHS if f"{x['number']}. {x['name']}" == txt), None)
        if surah:
            page = context.user_data.get("ghazi_quran_page", 0)
            context.user_data["ghazi_quran_page"] = page
            text = (
                f"📖 *سورة {surah['name']}*\n"
                f"🔢 رقمها: *{surah['number']}* | "
                f"📝 آياتها: *{surah['verses']}* آية | "
                f"🕌 *{surah['type']}*\n\n"
                f"اختر القراءة أو الاستماع:"
            )
            await update.effective_message.reply_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=ghazi_surah_keyboard(surah['number']),
            )
        else:
            await route_main(update, context, txt)

# ═══════════════════════════════════════════════════════
#  MAIN ROUTER
# ═══════════════════════════════════════════════════════

async def route_main(update, context, txt):
    if txt == "📖 القرآن الكريم":
        await show_quran_menu(update, context)
    elif txt == "🌅 الاذكار اليومية":
        await show_azkar_menu(update, context)
    elif txt == "🤲 دعاء":
        await show_random_dua(update, context)
    elif txt == "🌟 آية قرآنية":
        await show_random_aya(update, context)
    elif txt == "🕌 ادعية الانبياء":
        await show_prophets_list(update, context)
    elif txt == "🌙 السيرة النبوية":
        await show_seerah_menu(update, context)
    elif txt == "📚 قصة صحابي":
        await show_sahaba_list(update, context)
    elif txt == "💎 الباقيات الصالحات":
        await show_baqiyat(update, context)
    elif txt == "📜 قصة قرآنية":
        await show_quran_stories_list(update, context)
    elif txt == "🛡️ آية الكرسي":
        await show_ayat_karima(update, context)
    elif txt == "🔰 تحصين النفس":
        await show_tahsin_menu(update, context)
    elif txt == "📿 اسماء الله الحسنى":
        await show_asma_page(update, context, 0)
    elif txt == "📝 حديث نبوي":
        await show_hadith(update, context)
    elif txt == "🕌 اذكار بعد الصلاة":
        await show_after_prayer_azkar(update, context)
    elif txt == "⭐ فضائل الاعمال":
        await show_fadhail_menu(update, context)
    elif txt == "🌺 آداب اسلامية":
        await show_adab_menu(update, context)
    elif txt == "🙏 الاستغفار":
        await show_istighfar_menu(update, context)
    elif txt == "🕐 اوقات الصلاة":
        await show_prayer_countries(update, context)
    elif txt == "🎙️ صوتيه تكبيرات للسيد غازي عجاج":
        await send_ghazi_audio(update, context)
    elif txt == "🔔 تفعيل التنبيه":
        await enable_prayer_notify(update, context)
    elif txt == "🔕 إيقاف التنبيه":
        await disable_prayer_notify(update, context)
    elif txt == "🔄 دعاء آخر":
        await show_random_dua(update, context)
    elif txt == "🔄 آية أخرى":
        await show_random_aya(update, context)
    elif txt == "🔄 حديث آخر":
        await show_hadith(update, context)
    else:
        await update.effective_message.reply_text(
            "📋 *اختر ما تريد:*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_inline_menu_ghazi(),
        )

# ═══════════════════════════════════════════════════════
#  QURAN
# ═══════════════════════════════════════════════════════

GHAZI_SURAHS_PER_PAGE = 12
GHAZI_RECITERS = [
    ("محمد أيوب",          "https://server16.mp3quran.net/ayyoub2/Rewayat-Hafs-A-n-Assem/"),
    ("سعود الشريم",        "https://server7.mp3quran.net/shur/"),
    ("عبدالولي الأركاني",  "https://server6.mp3quran.net/arkani/"),
    ("علي جابر",           "https://server11.mp3quran.net/a_jbr/"),
    ("عبدالرحمن السديس",   "https://server11.mp3quran.net/sds/"),
    ("ماهر المعيقلي",      "https://server12.mp3quran.net/maher/"),
]

def ghazi_quran_keyboard(page=0):
    total_pages = (len(SURAHS) + GHAZI_SURAHS_PER_PAGE - 1) // GHAZI_SURAHS_PER_PAGE
    start = page * GHAZI_SURAHS_PER_PAGE
    end   = min(start + GHAZI_SURAHS_PER_PAGE, len(SURAHS))
    buttons = []
    for i in range(start, end, 3):
        row = []
        for s in SURAHS[i:min(i+3, end)]:
            row.append(InlineKeyboardButton(
                f"{s['number']}. {s['name']}",
                callback_data=f"gsurah_{s['number']}_{page}"
            ))
        buttons.append(row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("→ السابق", callback_data=f"gquran_p{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("التالي ←", callback_data=f"gquran_p{page+1}"))
    buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

def ghazi_surah_keyboard(surah_num):
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
        [InlineKeyboardButton("🔙 رجوع للسور", callback_data="ghazi_back_surahs")],
    ]
    return InlineKeyboardMarkup(buttons)

async def show_quran_menu(update, context):
    await show_surah_page(update, context, 0)

async def handle_ghazi_quran_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "noop":
        return
    if data == "ghazi_back_surahs":
        page = context.user_data.get("ghazi_quran_page", 0)
        await show_surah_page(update, context, page)


async def handle_ghazi_menu_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    _map = {
        "gmenu_quran":      show_quran_menu,
        "gmenu_azkar":      show_azkar_menu,
        "gmenu_dua":        show_random_dua,
        "gmenu_aya":        show_random_aya,
        "gmenu_prophets":   show_prophets_list,
        "gmenu_seerah":     show_seerah_menu,
        "gmenu_sahaba":     show_sahaba_list,
        "gmenu_baqiyat":    show_baqiyat,
        "gmenu_qstories":   show_quran_stories_list,
        "gmenu_kursi":      show_ayat_karima,
        "gmenu_tahsin":     show_tahsin_menu,
        "gmenu_hadith":     show_hadith,
        "gmenu_azkar_salah": show_after_prayer_azkar,
        "gmenu_fadhail":    show_fadhail_menu,
        "gmenu_adab":       show_adab_menu,
        "gmenu_istighfar":  show_istighfar_menu,
        "gmenu_prayer":     show_prayer_countries,
        "gmenu_takbeer":    send_ghazi_audio,
    }
    if data == "gmenu_asma":
        await show_asma_page(update, context, 0)
        return
    fn = _map.get(data)
    if fn:
        await fn(update, context)

async def route_quran(update, context, txt):
    if txt == "📚 قائمة السور الـ 114":
        await show_quran_menu(update, context)
    elif txt == "🎯 سور مشهورة":
        await show_selected_surahs(update, context)
    elif txt == "🌐 اقرأ القرآن (quran.com)":
        await show_quran_menu(update, context)

def surah_page_rows(page):
    per   = 9
    start = page * per
    end   = min(start + per, 114)
    total = (113 // per) + 1
    rows  = []
    for i in range(0, end - start, 3):
        rows.append([f"{s['number']}. {s['name']}" for s in SURAHS[start + i: start + i + 3]])
    nav = []
    if page > 0:  nav.append(f"◀️ السابق")
    nav.append(f"📄 {page+1}/{total}")
    if end < 114: nav.append(f"▶️ التالي")
    rows.append(nav)
    rows.append([BACK_MAIN])
    return rows, page, total

async def show_surah_page(update, context, page):
    rows, p, total = surah_page_rows(page)
    set_state(context, f"quran_surahs_{p}")
    await reply(
        update,
        f"📚 *قائمة السور — الصفحة {p+1}/{total}*\n\nاختر سورة:",
        kb(rows),
    )

async def route_surah_page(update, context, txt, s):
    page = int(s.split("_")[2])
    if txt == "▶️ التالي":
        await show_surah_page(update, context, page + 1)
    elif txt == "◀️ السابق":
        await show_surah_page(update, context, max(0, page - 1))
    elif txt.startswith("📄"):
        pass
    else:
        surah = next((x for x in SURAHS if f"{x['number']}. {x['name']}" == txt), None)
        if surah:
            context.user_data["ghazi_quran_page"] = page
            text = (
                f"📖 *سورة {surah['name']}*\n"
                f"🔢 رقمها: *{surah['number']}* | "
                f"📝 آياتها: *{surah['verses']}* آية | "
                f"🕌 *{surah['type']}*\n\n"
                f"اختر القراءة أو الاستماع:"
            )
            await update.effective_message.reply_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=ghazi_surah_keyboard(surah['number']),
            )
        else:
            await show_surah_page(update, context, page)

async def show_selected_surahs(update, context):
    selected = [1, 2, 18, 36, 55, 56, 67, 78, 112, 113, 114]
    rows = []
    for num in selected:
        s = next((x for x in SURAHS if x["number"] == num), None)
        if s:
            rows.append([f"{s['number']}. {s['name']} — {s['verses']} آية"])
    rows.append([BACK_MAIN])
    set_state(context, "quran_surahs_0")
    await reply(
        update,
        "🎯 *السور المشهورة*\n\nاختر:",
        kb(rows),
    )

# ═══════════════════════════════════════════════════════
#  AZKAR
# ═══════════════════════════════════════════════════════

AZKAR_MAP = {
    "🌅 أذكار الصباح":     "morning",
    "🌙 أذكار المساء":     "evening",
    "😴 أذكار النوم":      "sleep",
    "🕌 أذكار بعد الصلاة": "after_prayer",
}

async def show_azkar_menu(update, context):
    set_state(context, "azkar")
    rows = [[k] for k in AZKAR_MAP] + [[BACK_MAIN]]
    await reply(update, "🌅 *الأذكار اليومية*\n\nاختر:", kb(rows))

async def route_azkar_section(update, context, txt):
    key = AZKAR_MAP.get(txt)
    if key:
        section = AZKAR[key]
        lines = [f"*{section['title']}*\n"]
        for i, item in enumerate(section["items"], 1):
            lines.append(f"*{i}.* {item['text']}\n📊 _{item['count']}_\n")
        text = "\n".join(lines)
        if len(text) > 4096:
            text = text[:4090] + "..."
        await reply(update, text, kb([[BACK_MAIN]]))

async def show_after_prayer_azkar(update, context):
    section = AZKAR["after_prayer"]
    lines = [f"*{section['title']}*\n"]
    for i, item in enumerate(section["items"], 1):
        lines.append(f"*{i}.* {item['text']}\n📊 _{item['count']}_\n")
    text = "\n".join(lines)
    if len(text) > 4096:
        text = text[:4090] + "..."
    await reply(update, text, kb([[BACK_MAIN]]))

# ═══════════════════════════════════════════════════════
#  DUA
# ═══════════════════════════════════════════════════════

async def show_random_dua(update, context):
    title, dua = random.choice(DUAS)
    await reply(
        update,
        f"🤲 *{title}*\n\n❝ {dua} ❞",
        kb([["🔄 دعاء آخر"], [BACK_MAIN]]),
    )
    set_state(context, "main")

# ═══════════════════════════════════════════════════════
#  RANDOM AYA
# ═══════════════════════════════════════════════════════

async def show_random_aya(update, context):
    surah = random.choice(SURAHS)
    verse = random.randint(1, surah["verses"])
    await reply(
        update,
        f"🌟 *سورة {surah['name']} — الآية {verse}*\n\n"
        f"🌐 اقرأ الآية:\nhttps://quran.com/ar/{surah['number']}/{verse}",
        kb([["🔄 آية أخرى"], [BACK_MAIN]]),
    )
    set_state(context, "main")

# ═══════════════════════════════════════════════════════
#  PROPHETS
# ═══════════════════════════════════════════════════════

async def show_prophets_list(update, context):
    set_state(context, "prophets")
    prophet_list = list(PROPHETS.items())
    rows = []
    for i in range(0, len(prophet_list), 2):
        rows.append([f"{p['emoji']} {p['name']}" for _, p in prophet_list[i:i+2]])
    rows.append([BACK_MAIN])
    await reply(
        update,
        "🕌 *الأنبياء والمرسلون عليهم السلام*\n\nاختر نبياً:",
        kb(rows),
    )

async def route_prophet_list(update, context, txt):
    for key, p in PROPHETS.items():
        if txt == f"{p['emoji']} {p['name']}":
            set_state(context, "prophet_menu", pk=key)
            await show_prophet_menu(update, context, key)
            return
    await show_prophets_list(update, context)

async def show_prophet_menu(update, context, key):
    p = PROPHETS[key]
    rows = [
        ["📖 السيرة والقصة", "🤲 دعاؤه"],
        ["💑 زوجاته",         "👶 أولاده"],
        ["🔙 رجوع للأنبياء"],
    ]
    await reply(
        update,
        f"{p['emoji']} *{p['name']}*\n\nاختر:",
        kb(rows),
    )

async def route_prophet_menu(update, context, txt):
    key = context.user_data.get("pk")
    if not key:
        await show_main(update, context)
        return
    p = PROPHETS.get(key)
    if not p:
        await show_main(update, context)
        return

    back_row = kb([["🔙 رجوع للنبي"]])
    if txt == "📖 السيرة والقصة":
        await reply(update, f"{p['emoji']} *سيرة {p['name']}*\n\n{p['bio']}", back_row)
    elif txt == "🤲 دعاؤه":
        await reply(update, f"🤲 *دعاء {p['name']}*\n\n❝ {p['dua']} ❞", back_row)
    elif txt == "💑 زوجاته":
        await reply(update, f"💑 *زوجات {p['name']}*\n\n{p['wife']}", back_row)
    elif txt == "👶 أولاده":
        await reply(update, f"👶 *أولاد {p['name']}*\n\n{p['children']}", back_row)
    elif txt == "🔙 رجوع للنبي":
        await show_prophet_menu(update, context, key)
    elif txt == "🔙 رجوع للأنبياء":
        await show_prophets_list(update, context)

# ═══════════════════════════════════════════════════════
#  SEERAH
# ═══════════════════════════════════════════════════════

SEERAH_SECTIONS = {
    "👶 المولد والنشأة": (
        "👶 *المولد والنشأة الشريفة*\n\n"
        "وُلد النبي ﷺ في مكة المكرمة عام الفيل (571م) يوم الاثنين.\n\n"
        "👨 أبوه: عبدالله — توفي قبل ولادته\n"
        "👩 أمه: آمنة بنت وهب — توفيت وهو في السادسة\n"
        "👴 جده: عبدالمطلب — كفله حتى الثامنة\n"
        "🤝 عمه: أبو طالب — كفله بعد ذلك\n\n"
        "ارتضع عند حليمة السعدية في بني سعد. "
        "نشأ صادقاً أميناً حتى لُقِّب بـ'الأمين'."
    ),
    "📡 البعثة النبوية": (
        "📡 *البعثة النبوية*\n\n"
        "جاءه الوحي وهو في الأربعين في غار حراء. "
        "جاءه جبريل وقال: 'اقرأ'. فقال: 'ما أنا بقارئ'.\n\n"
        "أول ما نزل:\n"
        "﴿ اقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ ﴾\n\n"
        "استمر الوحي 23 سنة:\n"
        "• 13 سنة في مكة المكرمة\n"
        "• 10 سنوات في المدينة المنورة\n\n"
        "آخر ما نزل: ﴿ الْيَوْمَ أَكْمَلْتُ لَكُمْ دِينَكُمْ ﴾"
    ),
    "🏃 الهجرة المباركة": (
        "🏃 *الهجرة النبوية المباركة*\n\n"
        "هاجر ﷺ مع أبي بكر الصديق من مكة للمدينة عام 622م. "
        "اختبآ في غار ثور 3 أيام ثم وصلا المدينة.\n\n"
        "في المدينة أسّس ﷺ:\n"
        "🕌 المسجد النبوي الشريف\n"
        "🤝 المؤاخاة بين المهاجرين والأنصار\n"
        "📜 الدولة الإسلامية الأولى"
    ),
    "⚔️ الغزوات": (
        "⚔️ *الغزوات النبوية*\n\n"
        "غزا ﷺ 27 غزوة. أبرزها:\n\n"
        "🗡️ *بدر الكبرى* (2هـ) — أول معارك الإسلام الكبرى\n"
        "🗡️ *أحد* (3هـ) — ابتلاء وصبر\n"
        "🗡️ *الخندق* (5هـ) — حفر الخندق بفكرة سلمان\n"
        "🗡️ *خيبر* (7هـ) — فتح القلاع\n"
        "🗡️ *فتح مكة* (8هـ) — أعظم الانتصارات\n"
        "🗡️ *تبوك* (9هـ) — آخر الغزوات"
    ),
    "💑 زوجاته ﷺ": (
        "💑 *أمهات المؤمنين — زوجات النبي ﷺ*\n\n"
        "1. خديجة بنت خويلد ❤️ — أول زوجاته\n"
        "2. سودة بنت زمعة\n"
        "3. عائشة بنت أبي بكر\n"
        "4. حفصة بنت عمر\n"
        "5. زينب بنت خزيمة\n"
        "6. أم سلمة هند بنت أبي أمية\n"
        "7. زينب بنت جحش\n"
        "8. جويرية بنت الحارث\n"
        "9. أم حبيبة رملة بنت أبي سفيان\n"
        "10. صفية بنت حيي\n"
        "11. ميمونة بنت الحارث\n\n"
        "رضي الله عنهن جميعاً 🤍"
    ),
    "👶 أولاده ﷺ": (
        "👶 *أولاد النبي ﷺ*\n\n"
        "*من أمهم خديجة رضي الله عنها:*\n"
        "• القاسم\n• عبدالله\n• زينب\n• رقية\n• أم كلثوم\n• فاطمة الزهراء 🌹\n\n"
        "*من أمه مارية القبطية:*\n"
        "• إبراهيم — توفي رضيعاً\n\n"
        "كل أبنائه الذكور توفوا صغاراً رضي الله عنهم."
    ),
    "🌙 الوفاة الشريفة": (
        "🌙 *الوفاة الشريفة*\n\n"
        "توفي ﷺ في المدينة المنورة يوم الاثنين 12 ربيع الأول 11هـ.\n"
        "وعمره الشريف 63 سنة.\n\n"
        "توفي في بيت أم المؤمنين عائشة رضي الله عنها.\n\n"
        "آخر كلماته ﷺ:\n"
        "❝ اللَّهُمَّ الرَّفِيقَ الأَعْلَى ❞\n\n"
        "دُفن حيث توفي — ضمن المسجد النبوي الشريف.\n\n"
        "صلى الله عليه وسلم تسليماً كثيراً 🌙"
    ),
}

async def show_seerah_menu(update, context):
    set_state(context, "seerah")
    rows = [[k] for k in SEERAH_SECTIONS] + [[BACK_MAIN]]
    await reply(update, "🌙 *السيرة النبوية الشريفة*\n\nاختر:", kb(rows))

async def route_seerah(update, context, txt):
    content = SEERAH_SECTIONS.get(txt)
    if content:
        await reply(update, content, kb([["🔙 رجوع للسيرة"]]))
    elif txt == "🔙 رجوع للسيرة":
        await show_seerah_menu(update, context)

# ═══════════════════════════════════════════════════════
#  SAHABA
# ═══════════════════════════════════════════════════════

SAHABA_KEYS = list(SAHABA.keys())

def sahaba_inline_keyboard():
    rows = []
    for i in range(0, len(SAHABA_KEYS), 2):
        row = [InlineKeyboardButton(SAHABA_KEYS[i], callback_data=f"gsahaba_{i}")]
        if i + 1 < len(SAHABA_KEYS):
            row.append(InlineKeyboardButton(SAHABA_KEYS[i + 1], callback_data=f"gsahaba_{i+1}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="gsahaba_main")])
    return InlineKeyboardMarkup(rows)

async def show_sahaba_list(update, context):
    set_state(context, "main")
    await update.effective_message.reply_text(
        "📚 *قصص الصحابة الكرام رضي الله عنهم*\n\nاختر صحابياً:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=sahaba_inline_keyboard(),
    )

async def handle_ghazi_sahaba_callback(update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "gsahaba_main":
        await show_main(update, context)
        return
    if data == "gsahaba_back":
        await query.message.reply_text(
            "📚 *قصص الصحابة الكرام رضي الله عنهم*\n\nاختر صحابياً:",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=sahaba_inline_keyboard(),
        )
        return
    idx = int(data.split("_")[1])
    key = SAHABA_KEYS[idx]
    content = SAHABA[key]
    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع للصحابة", callback_data="gsahaba_back")]
    ])
    await query.message.reply_text(
        content,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=back_kb,
    )

async def route_sahaba(update, context, txt):
    pass

# ═══════════════════════════════════════════════════════
#  BAQIYAT
# ═══════════════════════════════════════════════════════

async def show_baqiyat(update, context):
    await reply(update, BAQIYAT, kb([[BACK_MAIN]]))

# ═══════════════════════════════════════════════════════
#  QURAN STORIES
# ═══════════════════════════════════════════════════════

async def show_quran_stories_list(update, context):
    set_state(context, "quran_stories")
    rows = [[name] for name in QURAN_STORIES] + [[BACK_MAIN]]
    await reply(update, "📜 *القصص القرآني*\n\nاختر قصة:", kb(rows))

async def route_quran_story(update, context, txt):
    content = QURAN_STORIES.get(txt)
    if content:
        await reply(update, content, kb([["🔙 رجوع للقصص"]]))
    elif txt == "🔙 رجوع للقصص":
        await show_quran_stories_list(update, context)

# ═══════════════════════════════════════════════════════
#  AYAT KARIMA
# ═══════════════════════════════════════════════════════

async def show_ayat_karima(update, context):
    await reply(update, AYAT_KARIMA, kb([[BACK_MAIN]]))

# ═══════════════════════════════════════════════════════
#  TAHSIN
# ═══════════════════════════════════════════════════════

async def show_tahsin_menu(update, context):
    set_state(context, "tahsin")
    rows = [[k] for k in TAHSIN] + [[BACK_MAIN]]
    await reply(update, "🔰 *تحصين النفس*\n\nاختر:", kb(rows))

async def route_tahsin(update, context, txt):
    content = TAHSIN.get(txt)
    if content:
        await reply(update, content, kb([["🔙 رجوع للتحصين"]]))
    elif txt == "🔙 رجوع للتحصين":
        await show_tahsin_menu(update, context)

# ═══════════════════════════════════════════════════════
#  ASMA ALLAH
# ═══════════════════════════════════════════════════════

async def show_asma_page(update, context, page):
    per   = 9
    start = page * per
    end   = min(start + per, 99)
    total = (98 // per) + 1
    names_slice = NAMES_OF_ALLAH[start:end]
    rows = []
    for i in range(0, len(names_slice), 3):
        rows.append([f"{n['number']}. {n['name']}" for n in names_slice[i:i+3]])
    nav = []
    if page > 0:  nav.append("◀️ السابق")
    nav.append(f"📄 {page+1}/{total}")
    if end < 99:  nav.append("▶️ التالي")
    rows.append(nav)
    rows.append([BACK_MAIN])
    set_state(context, f"asma_{page}")
    await reply(
        update,
        f"📿 *أسماء الله الحسنى — الصفحة {page+1}/{total}*\n\nاضغط الاسم لتعرف معناه:",
        kb(rows),
    )

async def route_asma(update, context, txt, s):
    if s.startswith("asma_back_"):
        page = int(s.split("_")[2])
    else:
        try:
            page = int(s.split("_")[-1])
        except (ValueError, IndexError):
            page = 0

    if txt == "▶️ التالي":
        await show_asma_page(update, context, page + 1)
    elif txt == "◀️ السابق":
        await show_asma_page(update, context, max(0, page - 1))
    elif txt.startswith("📄"):
        pass
    elif txt == "🔙 رجوع للأسماء":
        await show_asma_page(update, context, page)
    else:
        name_item = next(
            (n for n in NAMES_OF_ALLAH if f"{n['number']}. {n['name']}" == txt), None
        )
        if name_item:
            await reply(
                update,
                f"✨ *{name_item['name']}* ✨\n\n"
                f"🔢 الترتيب: {name_item['number']} من 99\n\n"
                f"📖 *المعنى:*\n{name_item['meaning']}\n\n"
                f"🤲 _يا {name_item['name']}، ارزقني من فضلك وأكرمني بكرمك_",
                kb([["🔙 رجوع للأسماء"]]),
            )
            set_state(context, f"asma_back_{page}")
        else:
            await show_asma_page(update, context, page)

# ═══════════════════════════════════════════════════════
#  HADITH
# ═══════════════════════════════════════════════════════

async def show_hadith(update, context):
    await reply(
        update,
        f"📝 *حديث نبوي شريف*\n\n{random.choice(HADITH_OF_DAY)}",
        kb([["🔄 حديث آخر"], [BACK_MAIN]]),
    )
    set_state(context, "main")

# ═══════════════════════════════════════════════════════
#  FADHAIL
# ═══════════════════════════════════════════════════════

async def show_fadhail_menu(update, context):
    set_state(context, "fadhail")
    rows = [[k] for k in FADHAIL] + [[BACK_MAIN]]
    await reply(update, "⭐ *فضائل الأعمال*\n\nاختر:", kb(rows))

async def route_fadhail(update, context, txt):
    content = FADHAIL.get(txt)
    if content:
        await reply(update, content, kb([["🔙 رجوع للفضائل"]]))
    elif txt == "🔙 رجوع للفضائل":
        await show_fadhail_menu(update, context)

# ═══════════════════════════════════════════════════════
#  ADAB
# ═══════════════════════════════════════════════════════

async def show_adab_menu(update, context):
    set_state(context, "adab")
    rows = [[k] for k in ADAB] + [[BACK_MAIN]]
    await reply(update, "🌺 *الآداب الإسلامية*\n\nاختر:", kb(rows))

async def route_adab(update, context, txt):
    content = ADAB.get(txt)
    if content:
        await reply(update, content, kb([["🔙 رجوع للآداب"]]))
    elif txt == "🔙 رجوع للآداب":
        await show_adab_menu(update, context)

# ═══════════════════════════════════════════════════════
#  ISTIGHFAR
# ═══════════════════════════════════════════════════════

ISTIGHFAR_MAP = {
    "👑 سيد الاستغفار":          0,
    "🤲 الاستغفار المأثور":      1,
    "✨ استغفار الإكثار":        2,
    "🌟 استغفار بين السجدتين":   3,
}

async def show_istighfar_menu(update, context):
    set_state(context, "istighfar")
    rows = [[k] for k in ISTIGHFAR_MAP] + [[BACK_MAIN]]
    await reply(update, "🙏 *الاستغفار*\n\nاختر:", kb(rows))

async def route_istighfar(update, context, txt):
    idx = ISTIGHFAR_MAP.get(txt)
    if idx is not None:
        await reply(update, ISTIGHFAR[idx], kb([["🔙 رجوع للاستغفار"]]))
    elif txt == "🔙 رجوع للاستغفار":
        await show_istighfar_menu(update, context)

# ═══════════════════════════════════════════════════════
#  PRAYER TIMES
# ═══════════════════════════════════════════════════════

async def show_prayer_countries(update, context):
    set_state(context, "prayer_countries")
    country_list = list(COUNTRIES.keys())
    rows = []
    for i in range(0, len(country_list), 2):
        rows.append(country_list[i:i+2])
    rows.append([BACK_MAIN])
    await reply(update, "🕐 *أوقات الصلاة*\n\nاختر الدولة:", kb(rows))

async def route_prayer_country(update, context, txt):
    code = COUNTRIES.get(txt)
    if not code:
        await show_prayer_countries(update, context)
        return
    context.user_data["country_code"] = code
    context.user_data["country_name"] = txt

    if code == "SA":
        set_state(context, "prayer_regions")
        regions = list(SA_REGIONS.keys())
        rows = [[r] for r in regions] + [["🔙 رجوع للدول"]]
        await reply(update, "🗺️ *اختر منطقتك في المملكة العربية السعودية:*", kb(rows))
    else:
        city_map = {
            "AE": "Abu Dhabi", "KW": "Kuwait",   "BH": "Manama",
            "QA": "Doha",      "OM": "Muscat",   "YE": "Sanaa",
            "JO": "Amman",     "SY": "Damascus", "LB": "Beirut",
            "IQ": "Baghdad",   "EG": "Cairo",    "LY": "Tripoli",
            "TN": "Tunis",     "DZ": "Algiers",  "MA": "Rabat",
            "SD": "Khartoum",  "SO": "Mogadishu","PK": "Islamabad",
            "TR": "Istanbul",  "ID": "Jakarta",  "MY": "Kuala Lumpur",
            "BD": "Dhaka",     "IN": "New Delhi","GB": "London",
            "US": "New York",  "FR": "Paris",    "DE": "Berlin",
            "CA": "Toronto",   "AU": "Sydney",
        }
        city = city_map.get(code, code)
        await update.effective_message.reply_text("⏳ جاري جلب أوقات الصلاة...")
        await fetch_prayer(update, context, code, city)

async def route_prayer_region(update, context, txt):
    if txt == "🔙 رجوع للدول":
        await show_prayer_countries(update, context)
        return
    cities = SA_REGIONS.get(txt)
    if cities:
        context.user_data["region_name"] = txt
        set_state(context, "prayer_cities")
        rows = []
        for i in range(0, len(cities), 2):
            rows.append(cities[i:i+2])
        rows.append(["🔙 رجوع للمناطق"])
        await reply(update, f"🏙️ *اختر مدينتك في {txt}:*", kb(rows))

async def route_prayer_city(update, context, txt):
    if txt == "🔙 رجوع للمناطق":
        set_state(context, "prayer_regions")
        rows = [[r] for r in SA_REGIONS] + [["🔙 رجوع للدول"]]
        await reply(update, "🗺️ *اختر منطقتك:*", kb(rows))
        return
    code = context.user_data.get("country_code", "SA")
    await update.effective_message.reply_text("⏳ جاري جلب أوقات الصلاة...")
    await fetch_prayer(update, context, code, txt)

async def fetch_prayer(update, context, country, city):
    method = PRAYER_METHODS.get(country, PRAYER_METHODS["DEFAULT"])
    url = (
        f"https://api.aladhan.com/v1/timingsByCity"
        f"?city={city}&country={country}&method={method}"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()

        if data.get("code") == 200:
            t = data["data"]["timings"]
            d = data["data"]["date"]
            hijri = f"{d['hijri']['day']} {d['hijri']['month']['ar']} {d['hijri']['year']} هـ"
            text = (
                f"🕌 *أوقات الصلاة*\n"
                f"📍 *{city}*\n\n"
                f"📅 {d['readable']}\n"
                f"🗓️ {hijri}\n\n"
                "─────────────────────\n"
                f"🌙 الفجر:   `{t.get('Fajr','─')}`\n"
                f"🌅 الشروق:  `{t.get('Sunrise','─')}`\n"
                f"☀️ الظهر:   `{t.get('Dhuhr','─')}`\n"
                f"🌤️ العصر:   `{t.get('Asr','─')}`\n"
                f"🌆 المغرب:  `{t.get('Maghrib','─')}`\n"
                f"🌙 العشاء:  `{t.get('Isha','─')}`\n"
                "─────────────────────\n\n"
                "_اللهم اجعلنا من المحافظين على الصلوات_"
            )
        else:
            text = f"⚠️ تعذّر جلب أوقات الصلاة لـ {city}. حاول مرة أخرى."
    except Exception as e:
        logger.error(f"Prayer API error: {e}")
        text = "⚠️ خطأ في الاتصال بالشبكة. حاول لاحقاً."

    if "⚠️" not in text:
        context.user_data["prayer_country"] = country
        context.user_data["prayer_city"]    = city
        notify_btn = "🔕 إيقاف التنبيه" if _has_notify_job(context) else "🔔 تفعيل التنبيه"
        await reply(update, text, kb([[BACK_MAIN], [notify_btn]]))
    else:
        await reply(update, text, kb([[BACK_MAIN]]))

# ═══════════════════════════════════════════════════════
#  PRAYER NOTIFICATIONS
# ═══════════════════════════════════════════════════════

def _notify_job_name(chat_id):
    return f"pray_daily_{chat_id}"

def _has_notify_job(context):
    chat_id = context._chat_id if hasattr(context, "_chat_id") else None
    if not chat_id:
        return False
    jobs = context.job_queue.get_jobs_by_name(_notify_job_name(chat_id))
    return len(jobs) > 0

async def send_prayer_alert(context):
    d = context.job.data
    await context.bot.send_message(
        chat_id=d["chat_id"],
        text=(
            f"🔔 *حان وقت الصلاة*\n\n"
            f"{d['prayer']}  —  `{d['time']}`\n"
            f"📍 {d['city']}\n\n"
            f"_حي على الصلاة، حي على الفلاح_\n\n"
            "🤲 اللهم اجعلنا من المحافظين على الصلوات"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )

async def prayer_daily_job(context):
    """يُجدول تنبيهات اليوم لجميع أوقات الصلاة."""
    d = context.job.data
    chat_id  = d["chat_id"]
    country  = d["country"]
    city     = d["city"]
    method   = PRAYER_METHODS.get(country, PRAYER_METHODS["DEFAULT"])
    url = (
        f"https://api.aladhan.com/v1/timingsByCity"
        f"?city={city}&country={country}&method={method}"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                api_data = await r.json()
        if api_data.get("code") == 200:
            t = api_data["data"]["timings"]
            prayers = {
                "🌙 الفجر":  t.get("Fajr"),
                "☀️ الظهر":  t.get("Dhuhr"),
                "🌤️ العصر":  t.get("Asr"),
                "🌆 المغرب": t.get("Maghrib"),
                "🌙 العشاء": t.get("Isha"),
            }
            now = datetime.now(_TZ)
            for name, ptime in prayers.items():
                if not ptime:
                    continue
                h, m = map(int, ptime[:5].split(":"))
                target = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if target > now:
                    delay = (target - now).total_seconds()
                    context.job_queue.run_once(
                        send_prayer_alert,
                        when=delay,
                        data={"chat_id": chat_id, "prayer": name,
                              "time": ptime[:5], "city": city},
                        name=f"pray_{chat_id}_{name}",
                    )
    except Exception as e:
        logger.error(f"Prayer daily job error: {e}")

async def enable_prayer_notify(update, context):
    chat_id = update.effective_chat.id
    country = context.user_data.get("prayer_country", "SA")
    city    = context.user_data.get("prayer_city", "")
    if not city:
        await reply(update, "⚠️ اختر مدينتك أولاً من قائمة أوقات الصلاة.", kb([[BACK_MAIN]]))
        return
    job_name = _notify_job_name(chat_id)
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()
    from datetime import time as dt_time
    context.job_queue.run_daily(
        prayer_daily_job,
        time=dt_time(0, 0, 0, tzinfo=_TZ),
        data={"chat_id": chat_id, "country": country, "city": city},
        name=job_name,
    )
    await prayer_daily_job.__wrapped__(context) if hasattr(prayer_daily_job, "__wrapped__") else None
    method = PRAYER_METHODS.get(country, PRAYER_METHODS["DEFAULT"])
    url = (
        f"https://api.aladhan.com/v1/timingsByCity"
        f"?city={city}&country={country}&method={method}"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as r:
                api_data = await r.json()
        if api_data.get("code") == 200:
            t = api_data["data"]["timings"]
            prayers_list = {
                "🌙 الفجر":  t.get("Fajr"),
                "☀️ الظهر":  t.get("Dhuhr"),
                "🌤️ العصر":  t.get("Asr"),
                "🌆 المغرب": t.get("Maghrib"),
                "🌙 العشاء": t.get("Isha"),
            }
            now = datetime.now(_TZ)
            for name, ptime in prayers_list.items():
                if not ptime:
                    continue
                h, m = map(int, ptime[:5].split(":"))
                target = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if target > now:
                    delay = (target - now).total_seconds()
                    context.job_queue.run_once(
                        send_prayer_alert,
                        when=delay,
                        data={"chat_id": chat_id, "prayer": name,
                              "time": ptime[:5], "city": city},
                        name=f"pray_{chat_id}_{name}",
                    )
    except Exception as e:
        logger.error(f"Enable notify fetch error: {e}")

    await reply(
        update,
        f"✅ *تم تفعيل تنبيه الصلاة*\n\n"
        f"📍 {city}\n\n"
        f"ستصلك رسالة عند كل أذان إن شاء الله 🕌",
        kb([[BACK_MAIN], ["🔕 إيقاف التنبيه"]]),
    )

async def disable_prayer_notify(update, context):
    chat_id = update.effective_chat.id
    job_name = _notify_job_name(chat_id)
    removed = 0
    for job in context.job_queue.get_jobs_by_name(job_name):
        job.schedule_removal()
        removed += 1
    for name in ["🌙 الفجر", "☀️ الظهر", "🌤️ العصر", "🌆 المغرب", "🌙 العشاء"]:
        for job in context.job_queue.get_jobs_by_name(f"pray_{chat_id}_{name}"):
            job.schedule_removal()
    await reply(
        update,
        "🔕 *تم إيقاف تنبيه الصلاة*\n\nيمكنك إعادة تفعيله في أي وقت.",
        kb([[BACK_MAIN]]),
    )

# ═══════════════════════════════════════════════════════
#  GHAZI AUDIO
# ═══════════════════════════════════════════════════════

_AUDIO_FILE_ID = None

async def send_ghazi_audio(update, context):
    global _AUDIO_FILE_ID
    caption = (
        "🎙️ *صوتيه تكبيرات للسيد غازي عجاج رحمه الله*\n\n"
        "🤍 اللهم كما أحييت ذكره بهذه التكبيرات، ارفع درجته في الجنة، "
        "واجعل نوره يضيء مرقده ولا ينطفئ."
    )
    try:
        if _AUDIO_FILE_ID:
            await update.effective_message.reply_audio(
                audio=_AUDIO_FILE_ID,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=kb([[BACK_MAIN]]),
            )
        else:
            with open("ghazi_ajaj.mp4", "rb") as f:
                msg = await update.effective_message.reply_audio(
                    audio=f,
                    caption=caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=kb([[BACK_MAIN]]),
                )
            _AUDIO_FILE_ID = msg.audio.file_id
        await update.effective_message.reply_text(DUA_GHAZI)
    except Exception as e:
        logger.error(f"Audio error: {e}")
        await reply(
            update,
            "⚠️ تعذّر تشغيل الصوتية. تأكد من رفع ملف ghazi_ajaj.mp4",
            kb([[BACK_MAIN]]),
        )

# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

PORT = int(os.environ.get("PORT", 8080))
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

class _HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *a):
        pass

def _start_health_server():
    try:
        server = HTTPServer(("0.0.0.0", PORT), _HealthHandler)
        logger.info(f"🌐 Health server on port {PORT}")
        server.serve_forever()
    except OSError:
        logger.warning(f"⚠️ Port {PORT} in use, skipping health server")

def _self_ping_loop():
    import time, urllib.request
    if not RENDER_URL:
        return
    time.sleep(60)
    while True:
        try:
            urllib.request.urlopen(f"{RENDER_URL}/", timeout=10)
            logger.info("✅ self-ping OK")
        except Exception as e:
            logger.warning(f"self-ping: {e}")
        time.sleep(300)

def main():
    if not TOKEN:
        raise ValueError("AZKAR_BOT_TOKEN is not set!")

    threading.Thread(target=_start_health_server, daemon=True).start()
    threading.Thread(target=_self_ping_loop,     daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("menu",   cmd_start))
    app.add_handler(CommandHandler("users",  cmd_users))
    app.add_handler(CommandHandler("ping",   cmd_ping))

    app.add_handler(CallbackQueryHandler(handle_ghazi_quran_callback, pattern=r"^(ghazi_back_surahs|noop)$"))
    app.add_handler(CallbackQueryHandler(handle_ghazi_sahaba_callback, pattern=r"^gsahaba_"))
    app.add_handler(CallbackQueryHandler(handle_ghazi_menu_callback, pattern=r"^gmenu_"))
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_msg
    ))

    import time as _time
    import telegram as _tg
    logger.info("🤖 البوت يعمل...")
    while True:
        try:
            app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
            break
        except _tg.error.Conflict:
            logger.warning("⚡ Conflict — نسخة أخرى تعمل، انتظر 40 ثانية...")
            _time.sleep(40)
        except Exception as e:
            logger.error(f"خطأ غير متوقع: {e}")
            raise

if __name__ == "__main__":
    main()
