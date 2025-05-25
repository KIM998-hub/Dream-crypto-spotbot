import telebot
import json
import time
from datetime import datetime
from pycoingecko import CoinGeckoAPI
import threading

# إعدادات البوت
TOKEN = "7653756929:AAFVze2LSOW_dw1NhxUTGlPtiQ5VN-mzRao"
CHANNEL_ID = -1002026068158  # معرف القناة Dream crypto spot signals
bot = telebot.TeleBot(TOKEN)
cg = CoinGeckoAPI()

# تحميل الإشارات
def load_signals():
    try:
        with open("signals.json", "r") as f:
            return json.load(f)
    except:
        return []

# حفظ الإشارات
def save_signals(signals):
    with open("signals.json", "w") as f:
        json.dump(signals, f, indent=2)

# حساب الأهداف والستوب
def calculate_targets(entry):
    targets = [round(entry * (1 + p), 4) for p in [0.019, 0.039, 0.086, 0.184, 0.242, 0.323, 0.4]]
    stop_loss = round(entry * 0.98, 4)
    return targets, stop_loss

# نشر التوصية
def send_signal(coin, entry, targets, stop_loss, timestamp):
    message = f"""صفقة جديدة

العملة: {coin.upper()}
سعر الدخول: {entry}
الستوب: {stop_loss}

الأهداف:
1️⃣ {targets[0]}
2️⃣ {targets[1]}
3️⃣ {targets[2]}
4️⃣ {targets[3]}
5️⃣ {targets[4]}
6️⃣ {targets[5]}
7️⃣ {targets[6]}

الوقت: {timestamp}
"""
    sent = bot.send_message(CHANNEL_ID, message)
    return sent.message_id

# مراقبة التحقق من الأهداف والستوب
def check_targets_loop():
    while True:
        signals = load_signals()
        for signal in signals:
            if len(signal["hit_targets"]) >= 7 or signal.get("hit_stop", False):
                continue

            coin_id = signal["coin"].lower()
            try:
                data = cg.get_price(ids=coin_id, vs_currencies='usd')
                price = data[coin_id]["usd"]
                now = datetime.now()
                entry = signal["entry"]

                # تحقق الأهداف
                for i, target in enumerate(signal["targets"]):
                    if i in signal["hit_targets"]:
                        continue
                    if price >= target:
                        signal["hit_targets"].append(i)
                        percent = round(((target - entry) / entry) * 100, 2)
                        elapsed = datetime.now() - datetime.strptime(signal["timestamp"], "%Y-%m-%d %H:%M:%S")
                        bot.send_message(
                            CHANNEL_ID,
                            f"""🎯 الهدف رقم {i+1} تحقق للعملة {signal['coin'].upper()}
السعر: {price}
النسبة: +{percent}%
المدة: {str(elapsed).split('.')[0]}""",
                            reply_to_message_id=signal["message_id"]
                        )

                # تحقق الستوب
                if not signal.get("hit_stop") and price <= signal["stop_loss"]:
                    signal["hit_stop"] = True
                    percent = round(((price - entry) / entry) * 100, 2)
                    elapsed = datetime.now() - datetime.strptime(signal["timestamp"], "%Y-%m-%d %H:%M:%S")
                    bot.send_message(
                        CHANNEL_ID,
                        f"""⛔ تم ضرب الستوب للعملة {signal['coin'].upper()}
السعر: {price}
النسبة: {percent}%
المدة: {str(elapsed).split('.')[0]}""",
                        reply_to_message_id=signal["message_id"]
                    )

            except Exception as e:
                print("خطأ:", e)

        save_signals(signals)
        time.sleep(60)

# أمر /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "أرسل اسم العملة وسعر الدخول بهذا الشكل:\nمثال: BTC 64200")

# استقبال التوصية
@bot.message_handler(func=lambda message: True)
def handle_signal(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            return

        coin = parts[0].lower()
        entry = float(parts[1])
        targets, stop_loss = calculate_targets(entry)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        signal = {
            "coin": coin,
            "entry": entry,
            "targets": targets,
            "stop_loss": stop_loss,
            "timestamp": timestamp,
            "message_id": None,
            "hit_targets": []
        }

        message_id = send_signal(coin, entry, targets, stop_loss, timestamp)
        signal["message_id"] = message_id

        signals = load_signals()
        signals.append(signal)
        save_signals(signals)

    except Exception as e:
        bot.reply_to(message, f"حدث خطأ: {e}")

# بدء المراقبة وتشغيل البوت
threading.Thread(target=check_targets_loop, daemon=True).start()
bot.infinity_polling()
