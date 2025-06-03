import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ✅ معلومات البوت والقناة
BOT_TOKEN = "7653756929:AAGnPLi2VY14mmcV5wsKFIOh8C5uvzfYy2s"
CHANNEL_ID = "-1002509422719"

# 🎯 تفعيل السجلات
logging.basicConfig(level=logging.INFO)

# 📢 دالة نشر التوصية
async def publish_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()
    
    if "/" not in text:
        await update.message.reply_text("❌ يرجى إرسال الزوج بالصيغة الصحيحة مثل: BTC/USDT")
        return

    pair = text
    signal_msg = (
        f"🚨🚨🚨 توصية جديدة 🔥🔥\n\n"
        f"🚀 الزوج: *{pair}*\n\n"
        f"📈 فرصة رائعة للدخول الآن! لا تفوتها 💸\n"
        f"🎯 تابعونا لمزيد من الصفقات الناجحة 👑\n\n"
        f"#Crypto #Signals #DreamCryptoBot"
    )

    await context.bot.send_message(chat_id=CHANNEL_ID, text=signal_msg, parse_mode="Markdown")

# 🛠️ إعداد التطبيق
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, publish_signal))

# 🚀 تشغيل البوت
if __name__ == '__main__':
    print("🚀 Bot is running and ready to publish signals...")
    app.run_polling()
