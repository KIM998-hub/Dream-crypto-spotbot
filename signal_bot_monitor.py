import telebot
import json
import time
import threading
import requests
from datetime import datetime

# ✅ بيانات البوت والقناة
TOKEN = "7653756929:AAGnPLi2VY14mmcV5wsKFIOh8C5uvzfYy2s"
CHANNEL_ID = -1002509422719  # Dream crypto spot signals
SIGNALS_FILE = "signals.json"

bot = telebot.TeleBot(TOKEN)
symbol_to_id_cache = {}

def save_signal(signal):
    try:
        with open(SIGNALS_FILE, "r") as f:
            signals = json.load(f)
    except:
        signals = []
    signals.append(signal)
    with open(SIGNALS_FILE, "w") as f:
        json.dump(signals, f, indent=2)

def load_signals():
    try:
        with open(SIGNALS_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def format_percentage(entry, target):
    return round(((target - entry) / entry) * 100, 2)

def get_price(symbol):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usdt"
        res = requests.get(url)
        time.sleep(1.5)
        price = res.json()[symbol]["usdt"]
        print(f"🔍 السعر الحالي لـ {symbol} هو: {price}")
        return price
    except Exception as e:
        print(f"❌ خطأ في get_price لـ {symbol}: {e}")
        return None

def coin_symbol_to_id(coin):
    coin = coin.lower()
    if coin in symbol_to_id_cache:
        return symbol_to_id_cache[coin]

    url = "https://api.coingecko.com/api/v3/coins/list"
    try:
        response = requests.get(url)
        time.sleep(1.5)
        if response.status_code != 200:
            print(f"❌ CoinGecko API فشل: {response.status_code}")
            return None
        data = response.json()
        for item in data:
            if item["symbol"] == coin:
                symbol_to_id_cache[coin] = item["id"]
                return item["id"]
        print(f"❌ لم يتم إيجاد Coin ID لـ {coin}")
    except Exception as e:
        print(f"❌ خطأ في CoinGecko: {e}")
    return None

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "❌ يرجى إرسال العملة وسعر الدخول فقط، مثل: `SOL 162.3`")
            return

        coin, entry_price = parts
        coin = coin.upper()
        entry_price = float(entry_price)
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

def monitor_targets():
    print("🔁 بدأ مراقبة الأسعار...")
    while True:
        signals = load_signals()
        print(f"📡 جاري فحص {len(signals)} توصيات...")

        updated = False

        for signal in signals:
            if len(signal["hit"]) >= len(signal["targets"]) + 1:
                continue

            coin_id = coin_symbol_to_id(signal["coin"])
            if not coin_id:
                print(f"❌ فشل في الحصول على ID للعملة {signal['coin']}")
                continue

            price = get_price(coin_id)
            if not price:
                print(f"❌ لم يتم جلب السعر لـ {signal['coin']}")
                continue

            entry = signal["entry"]
            now = time.time()
            elapsed = now - signal["start_time"]
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)

            def send_hit(msg):
                bot.send_message(
                    CHANNEL_ID,
                    msg,
                    reply_to_message_id=signal["msg_id"],
                    parse_mode="Markdown"
                )
                time.sleep(1.5)

            # تحقق من الأهداف
            for i, target in enumerate(signal["targets"]):
                if i in signal["hit"]:
                    continue
                if price >= target:
                    percent = format_percentage(entry, target)
                    msg = f"🎯 تم تحقيق *هدف {i+1}* بنسبة *{percent}%* بعد {hours}h {minutes}m."
                    send_hit(msg)
                    signal["hit"].append(i)
                    updated = True
                    break

            # تحقق من الستوب
            if "stop" not in signal["hit"] and price <= signal["stop_loss"]:
                percent = format_percentage(entry, signal["stop_loss"])
                msg = f"🛑 تم ضرب وقف الخسارة بخسارة *{abs(percent)}%* بعد {hours}h {minutes}m."
                send_hit(msg)
                signal["hit"].append("stop")
                updated = True

        if updated:
            with open(SIGNALS_FILE, "w") as f:
                json.dump(signals, f, indent=2)

        time.sleep(60)

# تشغيل مراقبة الأهداف
threading.Thread(target=monitor_targets, daemon=True).start()

# تشغيل البوت عبر polling
print("🤖 البوت يعمل الآن ب polling وينتظر الأوامر...")
bot.infinity_polling()
