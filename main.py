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

# Load signals
def load_signals():
    try:
        with open(SIGNALS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Save signals
def save_signals(signals):
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(signals, f, indent=4)

# Fetch coin list
def fetch_coin_list():
    print("Fetching coin list...")
    url = 'https://api.coingecko.com/api/v3/coins/list'
    response = requests.get(url)
    if response.status_code == 200:
        print("Coin list fetched successfully.")
        return {coin['symbol'].upper(): coin['id'] for coin in response.json()}
    print("Failed to fetch coin list.")
    return {}

COIN_LIST = fetch_coin_list()

# Get current price
def get_price(coin_id):
    try:
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd'
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get(coin_id, {}).get('usd')
    except Exception as e:
        print(f"Error getting price for {coin_id}: {e}")
    return None

# Monitor prices
def monitor_prices():
    while True:
        signals = load_signals()
        updated = False
        for signal in signals:
            if signal["hit_stop"] or len(signal["hit_targets"]) == len(signal["targets"]):
                continue

            coin_id = signal["coin_id"]
            current_price = get_price(coin_id)
            print(f"[{signal['coin']}] Current price: {current_price}")

            if not current_price:
                print(f"Skipping {signal['coin']} due to missing price.")
                continue

            now = time.time()
            duration = lambda ts: round((now - ts) / 60)

            # Check targets
            for i, target in enumerate(signal["targets"]):
                if i not in signal["hit_targets"] and current_price >= target:
                    try:
                        msg = f"""🎯 الهدف رقم {i+1} تحقق لعملة {signal["coin"]}!

المدة: {duration(signal["timestamp"])} دقيقة.
السعر الحالي: {current_price}
الهدف: {target}
"""
                        bot.send_message(CHANNEL_ID, msg, reply_to_message_id=signal["message_id"])
                        print(f"[{signal['coin']}] Target {i+1} hit.")
                        signal["hit_targets"].append(i)
                        updated = True
                        break
                    except Exception as e:
                        print(f"Error sending target message: {e}")

            # Check stop-loss
            if not signal["hit_stop"] and current_price <= signal["stop_loss"]:
                try:
                    msg = f"""❌ تم ضرب وقف الخسارة لعملة {signal["coin"]}

المدة: {duration(signal["timestamp"])} دقيقة.
السعر الحالي: {current_price}
وقف الخسارة: {signal["stop_loss"]}
"""
                    bot.send_message(CHANNEL_ID, msg, reply_to_message_id=signal["message_id"])
                    print(f"[{signal['coin']}] Stop-loss hit.")
                    signal["hit_stop"] = True
                    updated = True
                except Exception as e:
                    print(f"Error sending stop-loss message: {e}")

        if updated:
            save_signals(signals)
            print("Signals updated.")

        time.sleep(60)

@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "يرجى إرسال: COIN PRICE\nمثال: BTC 62000")
            return

        coin = parts[0].upper()
        price = float(parts[1])

        if coin not in COIN_LIST:
            bot.reply_to(message, f"العملة {coin} غير مدعومة حالياً.")
            return

        coin_id = COIN_LIST[coin]
        stop_loss = round(price * 0.98, 6)
        targets = [round(price * (1 + t / 100), 6) for t in TARGETS]

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
        print(f"[{coin}] Signal posted.")

        new_signal = {
            "coin": coin,
            "coin_id": coin_id,
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
        print(f"[{coin}] Signal saved.")

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")
        print(f"Error in handle_message: {e}")

# Start monitoring in thread
threading.Thread(target=monitor_prices, daemon=True).start()

print("Bot is polling...")
bot.polling()
