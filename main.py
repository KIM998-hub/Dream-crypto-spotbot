import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = "7653756929:AAGnPLi2VY14mmcV5wsKFIOh8C5uvzfYy2s"
CHANNEL_ID = "-1002509422719"

TARGET_PERCENTAGES = [1.9, 3.9, 8.6, 18.4, 24.2, 32.3, 40.0]

logging.basicConfig(level=logging.INFO)

def calculate_targets(entry_price: float):
    targets = [round(entry_price * (1 + pct / 100), 2) for pct in TARGET_PERCENTAGES]
    stop_loss = round(entry_price * 0.98, 2)
    return stop_loss, targets

def format_signal(pair: str, entry_price: float, stop_loss: float, targets: list):
    message = f"""🚀 توصية جديدة (سبوت) 🚀

📈 الزوج: {pair.upper()}
🎯 نقطة الدخول: {entry_price} USDT
🛡️ وقف الخسارة: {stop_loss} USDT

🎯 أهداف الربح:"""
    for i, target in enumerate(targets, start=1):
        pct = TARGET_PERCENTAGES[i - 1]
        message += f"\n{i}️⃣ {target} USDT (+{pct}%)"
    
    message += "\n\n📢 إدارة رأس المال مسؤوليتك، التزم بخطتك! 🧠"
    return message

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("⚠️ الرجاء إرسال التوصية بهذا الشكل:\nBTC/USDT 68300")
            return

        pair = parts[0]
        entry_price = float(parts[1])
        stop_loss, targets = calculate_targets(entry_price)
        signal_message = format_signal(pair, entry_price, stop_loss, targets)

        await context.bot.send_message(chat_id=CHANNEL_ID, text=signal_message)
        await update.message.reply_text("✅ تم نشر التوصية بنجاح.")
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء معالجة التوصية.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
