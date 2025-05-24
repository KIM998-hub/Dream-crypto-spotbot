import os
import json
import telebot
import requests
from flask import Flask, request
from datetime import datetime
import threading
import time

# Telegram config
TOKEN = "7653756929:AAFVze2LSOW_dw1NhxUTGlPtiQ5VN-mzRao"
CHANNEL_ID = "@Dreamcryptospot"
bot = telebot.TeleBot(TOKEN)

# Price monitor settings
CHECK_INTERVAL = 60  # seconds

# Create Flask app
app = Flask(__name__)

# Signal data storage
SIGNALS_FILE = "signals.json"
if not os.path.exists(SIGNALS_FILE):
    with open(SIGNALS_FILE, "w") as f:
        json.dump({}, f)

# Load signals
def load_signals():
    with open(SIGNALS_FILE, "r") as f:
        return json.load(f)

# Save signals
def save_signals(data):
    with open(SIGNALS_FILE, "w") as f:
        json.dump(data, f, indent=2)

# Create signal message
def create_signal_message(coin, entry, sl, targets):
    message = f"تم نشر توصية جديدة\n\n"
    message += f"العملة: {coin.upper()}\n"
    message += f"منطقة الدخول: {entry:.4f}\n"
    message += f"وقف الخسارة: {sl:.4f}\n\n"
    for i, t in enumerate(targets):
        message += f"الهدف {i+1}: {t:.4f}\n"
    message += "\nبالتوفيق!"
    return message

# Get price from CoinGecko
def get_price(coin):
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
        response = requests.get(url).json()
        return float(response[coin]["usd"])
    except:
        return None

# Monitor thread
def price_monitor():
    while True:
        signals = load_signals()
        updated = False
        for coin, data in signals.items():
            if data.get("hit"):
                continue
            price = get_price(data["cg_id"])
            if not price:
                continue

            now = time.time()
            duration = int(now - data["timestamp"])
            minutes = duration // 60

            for i, target in enumerate(data["targets"]):
                if not data["hits"][i] and price >= target:
                    msg = f"🎯 تم تحقيق الهدف {i+1} لعملة {coin.upper()} خلال {minutes} دقيقة"
                    bot.send_message(CHANNEL_ID, msg, reply_to_message_id=data["msg_id"])
                    data["hits"][i] = True
                    updated = True

            if not data["sl_hit"] and price <= data["stoploss"]:
                msg = f"⛔ تم ضرب وقف الخسارة لعملة {coin.upper()} خلال {minutes} دقيقة"
                bot.send_message(CHANNEL_ID, msg, reply_to_message_id=data["msg_id"])
                data["sl_hit"] = True
                updated = True

            if all(data["hits"]) or data["sl_hit"]:
                data["hit"] = True

        if updated:
            save_signals(signals)
        time.sleep(CHECK_INTERVAL)

# Start monitor thread
threading.Thread(target=price_monitor, daemon=True).start()

# Handle signal messages
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            return
        coin = parts[0].lower()
        entry = float(parts[1])
        sl = round(entry * 0.98, 4)
        targets = [round(entry * r, 4) for r in [1.019, 1.039, 1.086, 1.184, 1.242, 1.323, 1.40]]

        # Get CoinGecko ID
        cg_data = requests.get("https://api.coingecko.com/api/v3/coins/list").json()
        match = next((c for c in cg_data if c["symbol"].lower() == coin), None)
        if not match:
            bot.reply_to(message, f"لم أتمكن من التعرف على العملة: {coin.upper()}")
            return
        cg_id = match["id"]

        msg = create_signal_message(coin, entry, sl, targets)
        sent = bot.send_message(CHANNEL_ID, msg)
        msg_id = sent.message_id

        # Save signal
        signals = load_signals()
        signals[coin] = {
            "coin": coin,
            "cg_id": cg_id,
            "entry": entry,
            "stoploss": sl,
            "targets": targets,
            "hits": [False] * len(targets),
            "sl_hit": False,
            "hit": False,
            "timestamp": time.time(),
            "msg_id": msg_id
        }
        save_signals(signals)

    except Exception as e:
        print("Error:", e)

# Webhook route
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

# Root route
@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

# Run
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
