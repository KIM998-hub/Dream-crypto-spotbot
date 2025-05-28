import telebot
import json
import time
from datetime import datetime
import os
from utils.image_generator import generate_signal_image
from utils.signal_formatter import format_signal_message
from utils.price_monitor import start_monitoring

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

bot = telebot.TeleBot(BOT_TOKEN)

# تحميل الإشارات السابقة من الملف
if os.path.exists("signals.json"):
    with open("signals.json", "r") as f:
        signals = json.load(f)
else:
    signals = {}

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "أهلاً بك! أرسل اسم العملة وسعر الدخول فقط (مثال: ETH 2745)")

@bot.message_handler(func=lambda message: True)
def handle_signal(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ صيغة غير صحيحة. أرسل اسم العملة وسعر الدخول فقط (مثال: ETH 2745)")
            return

        coin = parts[0].upper()
        entry = float(parts[1])

        stop_loss = round(entry * 0.98, 4)
        targets = [
            round(entry * 1.019, 4),
            round(entry * 1.039, 4),
            round(entry * 1.086, 4),
            round(entry * 1.184, 4),
            round(entry * 1.242, 4),
            round(entry * 1.323, 4),
            round(entry * 1.4, 4)
        ]

        timestamp = time.time()
        signal_id = str(int(timestamp))

        signals[signal_id] = {
            "coin": coin,
            "entry": entry,
            "stop_loss": stop_loss,
            "targets": targets,
            "timestamp": timestamp,
            "status": "active",
            "chat_id": CHANNEL_ID,
            "message_id": None
        }

        with open("signals.json", "w") as f:
            json.dump(signals, f, indent=4)

        # إرسال الصورة
        image_path = generate_signal_image(coin, entry, stop_loss, targets)
        with open(image_path, 'rb') as photo:
            sent_message = bot.send_photo(CHANNEL_ID, photo)

        # إرسال النص
        text = format_signal_message(coin, entry, stop_loss, targets)
        reply_msg = bot.send_message(CHANNEL_ID, text, reply_to_message_id=sent_message.message_id)

        # تحديث الرسالة ID للربط لاحقًا
        signals[signal_id]["message_id"] = reply_msg.message_id
        with open("signals.json", "w") as f:
            json.dump(signals, f, indent=4)

        # بدء المراقبة الآلية
        start_monitoring(coin, entry, stop_loss, targets, signal_id, timestamp, CHANNEL_ID, reply_msg.message_id, bot)

    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {str(e)}")

# لا داعي لهذا السطر في Railway
# bot.remove_webhook()

print("Bot is polling...")
bot.infinity_polling()
