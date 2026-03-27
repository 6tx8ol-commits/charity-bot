import TelegramBot from 'node-telegram-bot-api';

const token = '8691783072:AAE5cVJOPL6LWqk6Bp_qEDJw1JYLlxTXSGw'; 

const bot = new TelegramBot(token, { polling: true });

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

    if (text === "📿 الأذكار اليومية") {
        const athkar = `📿 أذكار المساء:\n\n1. "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ".\n2. "آية الكرسي".\n3. "سُبْحَانَ اللَّهِ وَبِحَمْدِهِ" (100 مرة).`;
        bot.sendMessage(chatId, athkar);
    }
});

console.log("روبوت الخير شغال...");
