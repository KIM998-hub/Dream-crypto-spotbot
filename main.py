import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TOKEN = "7653756929:AAGnPLi2VY14mmcV5wsKFIOh8C5uvzfYy2s"
CHANNEL_ID = "-1002509422719"

TARGET_PERCENTAGES = [1.9, 3.9, 8.6, 18.4, 24.2, 32.3, 40.0]

logging.basicConfig(level=logging.INFO)

def calculate_targets(entry_price: float, decimals: int):
    multiplier = lambda pct: round(entry_price * (1 + pct / 100), decimals)
    targets = [multiplier(pct) for pct in TARGET_PERCENTAGES]
    stop_loss = round(entry_price * 0.98, decimals)
    return stop_loss, targets

def get_decimal_places(number_str: str):
    if '.' in number_str:
        return len(number_str.split('.')[1])
    return 0

def format_signal(coin: str, entry_price: float, stop_loss: float, targets: list, decimals: int):
    def fmt(val): return f"{val:.{decimals}f}"

    message = (
        "**🚀 New Spot Signal 🚨**\n\n"
        f"📊 **Coin:** {coin.upper()}\n"
        f"🎯 **Entry Point:** {fmt(entry_price)}\n"
        f"🛡️ **Stop Loss:** {fmt(stop_loss)}\n\n"
        "🎯 **Targets:**"
    )
    for i, target in enumerate(targets, start=1):
        message += f"\n{i}️⃣ {fmt(target)}"
    return message

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        parts = text.split()
        if len(parts) != 2:
            await update.message.reply_text("⚠️ Please send the signal in this format:\nCOIN/USDT 0.0000000")
            return

        coin = parts[0]
        entry_price_str = parts[1]
        entry_price = float(entry_price_str)
        decimals = get_decimal_places(entry_price_str)

        stop_loss, targets = calculate_targets(entry_price, decimals)
        signal_message = format_signal(coin, entry_price, stop_loss, targets, decimals)

        await context.bot.send_message(chat_id=CHANNEL_ID, text=signal_message, parse_mode="Markdown")
        await update.message.reply_text("✅ Signal published successfully.")
    except Exception as e:
        logging.error(f"Error: {e}")
        await update.message.reply_text("❌ An error occurred while processing the signal.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
