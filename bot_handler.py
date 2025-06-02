import telebot
import json
import time
import re

# ✅ بيانات البوت والقناة
TOKEN = "7653756929:AAGnPLi2VY14mmcV5wsKFIOh8C5uvzfYy2s"
CHANNEL_ID = -1002509422719  # Dream crypto spot signals
SIGNALS_FILE = "signals.json"

bot = telebot.TeleBot(TOKEN)

def save_signal(signal):
    try:
        with open(SIGNALS_FILE, "r") as f:
            signals = json.load(f)
    except:
        signals = []
    signals.append(signal)
    with open(SIGNALS_FILE, "w") as f:
        json.dump(signals, f, indent=2)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        parts = re.split(r'[\s/]+', message.text.strip())
        if len(parts) != 3 or parts[1].upper() != "USDT":
            bot.reply_to(message, "❌ يرجى إرسال التوصية بهذا الشكل: `BTC/USDT 105000`")
            return

        coin = parts[0].upper()
        entry_price = float(parts[2])
        stop_loss = round(entry_price * 0.98, 4)
        targets = [
            round(entry_price * (1 + p), 4)
            for p in [0.019, 0.039, 0.086, 0.184, 0.242, 0.323, 0.40]
        ]
        timestamp = time.time()

        signal = {
            "coin": coin,
            "entry": entry_price,
            "stop_loss": stop_loss,
            "targets": targets,
            "start_time": timestamp,
            "msg_id": None,
            "hit": []
        }

        text = f"""🚀 توصية عملة: {coin}

💰 سعر الدخول: `{entry_price}`
📉 وقف الخسارة: `{stop_loss}`

🎯 الأهداف:
""" + "\n".join([f"🎯 هدف {i+1}: `{t}`" for i, t in enumerate(targets)])

        sent = bot.send_message(CHANNEL_ID, text, parse_mode="Markdown")
        time.sleep(1.5)
        signal["msg_id"] = sent.message_id
        save_signal(signal)
        bot.reply_to(message, "✅ تم نشر التوصية بنجاح!")
        time.sleep(1.5)

    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {e}")
        time.sleep(1.5)

print("🤖 البوت يعمل الآن ب polling وينتظر الأوامر...")
bot.infinity_polling()
