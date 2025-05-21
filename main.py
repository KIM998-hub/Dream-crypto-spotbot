import telebot
import json
import time
import threading
import requests
from datetime import datetime

BOT_TOKEN = '7653756929:AAFVze2LSOW_dw1NhxUTGlPtiQ5VN-mzRao'
CHANNEL_ID = '@Dreamcryptospotsignals'
TARGETS = [1.9, 3.9, 8.6, 18.4, 24.2, 32.3, 40]
bot = telebot.TeleBot(BOT_TOKEN)
SIGNALS_FILE = 'signals.json'

# Load signals from file
def load_signals():
    try:
        with open(SIGNALS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save signals to file
def save_signals(signals):
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(signals, f, indent=4)

# Fetch current price using CoinGecko
def get_price(coin_id):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd'
    response = requests.get(url)
    data = response.json()
    return data.get(coin_id, {}).get('usd', None)

# Convert coin symbol to CoinGecko ID
def get_coin_id(symbol):
    mapping = {
        'BTC': 'bitcoin',
        'ETH': 'ethereum',
        'BNB': 'binancecoin',
        'SOL': 'solana',
        'XRP': 'ripple',
        'DOGE': 'dogecoin',
        'ADA': 'cardano',
        'AVAX': 'avalanche-2'
    }
    return mapping.get(symbol.upper())

# Monitor prices and send alerts
def monitor_prices():
    while True:
        signals = load_signals()
        updated = False
        for signal in signals:
            if signal["hit_stop"] or len(signal["hit_targets"]) == len(signal["targets"]):
                continue

            coin_id = get_coin_id(signal["coin"])
            if not coin_id:
                continue

            current_price = get_price(coin_id)
            if not current_price:
                continue

            now = time.time()
            duration = lambda ts: round((now - ts) / 60)

            # Check targets
            for i, target in enumerate(signal["targets"]):
                if i not in signal["hit_targets"] and current_price >= target:
                    msg = f"""🎯 الهدف رقم {i+1} تحقق لعملة {signal["coin"]}!

المدة: {duration(signal["timestamp"])} دقيقة.
السعر الحالي: {current_price}
الهدف: {target}
"""
                    bot.send_message(CHANNEL_ID, msg, reply_to_message_id=signal["message_id"])
                    signal["hit_targets"].append(i)
                    updated = True
                    break

            # Check stop-loss
            if not signal["hit_stop"] and current_price <= signal["stop_loss"]:
                msg = f"""❌ تم ضرب وقف الخسارة لعملة {signal["coin"]}

المدة: {duration(signal["timestamp"])} دقيقة.
السعر الحالي: {current_price}
وقف الخسارة: {signal["stop_loss"]}
"""
                bot.send_message(CHANNEL_ID, msg, reply_to_message_id=signal["message_id"])
                signal["hit_stop"] = True
                updated = True

        if updated:
            save_signals(signals)

        time.sleep(60)

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "Please send: COIN PRICE\nExample: BTC 62000")
            return

        coin = parts[0].upper()
        price = float(parts[1])
        stop_loss = round(price * 0.98, 4)
        targets = [round(price * (1 + t / 100), 4) for t in TARGETS]

        signal_text = f"""#SPOT SIGNAL

عملة: {coin}
سعر الدخول: {price}
وقف الخسارة: {stop_loss}

الأهداف:
1. {targets[0]}
2. {targets[1]}
3. {targets[2]}
4. {targets[3]}
5. {targets[4]}
6. {targets[5]}
7. {targets[6]}

#DreamCryptoSpot
"""
        sent = bot.send_message(CHANNEL_ID, signal_text)
        new_signal = {
            "coin": coin,
            "entry": price,
            "stop_loss": stop_loss,
            "targets": targets,
            "hit_targets": [],
            "hit_stop": False,
            "timestamp": time.time(),
            "message_id": sent.message_id
        }

        signals = load_signals()
        signals.append(new_signal)
        save_signals(signals)

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# Start price monitoring thread
threading.Thread(target=monitor_prices, daemon=True).start()

bot.polling()
