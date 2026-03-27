import TelegramBot from 'node-telegram-bot-api';

// ضع التوكن حقك هنا بين العلامتين
const token = 'ضع_هنا_التوكن_الذي_نسخته_من_ريبلت'; 

const bot = new TelegramBot(token, { polling: true });

// القائمة الرئيسية (نفس تصميمك الفخم)
const mainMenu = {
    reply_markup: {
        keyboard: [
            [{ text: "📖 القرآن الكريم" }],
            [{ text: "📿 الأذكار اليومية" }, { text: "🤲 دعاء" }],
            [{ text: "🌹 أدعية الأنبياء" }, { text: "✨ آية قرآنية" }],
            [{ text: "⭐ قصة صحابي" }, { text: "🕊️ مسيرة الأنبياء" }],
            [{ text: "📜 قصة قرآنية" }, { text: "📚 السيرة النبوية" }],
            [{ text: "🔵 آية الكرسي" }, { text: "💚 الباقيات الصالحات" }],
            [{ text: "🕒 أوقات الصلاة" }, { text: "💙 الاستغفار" }]
        ],
        resize_keyboard: true
    }
};

bot.onText(/\/start/, (msg) => {
    const welcomeMsg = `أهلاً بك 🤍\n\nهذا بوت صدقة جارية لـ غازي عجاج\nاللهم اغفر له وارحمه واجعلها نوراً له في قبره 🤍\n\nاختر من الأزرار بالأسفل 👇`;
    bot.sendMessage(msg.chat.id, welcomeMsg, mainMenu);
});

bot.on('message', (msg: any) => {
    const chatId = msg.chat.id;
    const text = msg.text;

    if (text === "📖 القرآن الكريم") {
        bot.sendMessage(chatId, "يمكنك قراءة القرآن الكريم كاملاً عبر الرابط التالي:\nhttps://quran.com", {
            reply_markup: {
                inline_keyboard: [[{ text: "فتح المصحف الإلكتروني 🌐", url: "https://quran.com" }]]
            }
        });
    }

    if (text === "🕒 أوقات الصلاة") {
        const prayerTimes = `🕌 أوقات الصلاة — تبوك\n\nالفجر —— 05:08\nالظهر —— 12:39\nالعصر —— 16:08\nالمغرب —— 18:49\nالعشاء —— 20:19\n\n— صدقة جارية لغازي عجاج، اللهم اغفر له`;
        bot.sendMessage(chatId, prayerTimes);
    }
});

console.log("روبوت الخير بدأ العمل...");
