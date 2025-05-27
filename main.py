import telebot
import json
import os
import time
import threading
from datetime import datetime
from pycoingecko import CoinGeckoAPI

TOKEN = '7653756929:AAFVze2LSOW_dw1NhxUTGlPtiQ5VN-mzRao'
CHANNEL_ID = -1002509422719
SIGNALS_FILE = 'signals.json'

bot = telebot.TeleBot(TOKEN)
cg = CoinGeckoAPI()

TARGET_PERCENTS = [1.9, 3.9, 8.6, 18.4, 24.2, 32.3, 40.0]
STOP_LOSS_PERCENT = 2

def get_coin_id_from_symbol(symbol):
    coins = cg.get_coins_list()
    for coin in coins:
        if coin['symbol'].lower() == symbol.lower():
            return coin['id']
    raise ValueError(f"Coin symbol '{symbol}' not found on CoinGecko")

def load_signals():
    if not os.path.exists(SIGNALS_FILE):
        return []
    with open(SIGNALS_FILE, 'r') as f:
        return json.load(f)

def save_signals(signals):
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(signals, f, indent=2)

def format_signal_text(coin, entry, targets, stop_loss):
    text = f"""Spot Signal

Coin: {coin.upper()}
Entry Zone: {entry}

Targets:
"""
    for i, target in enumerate(targets):
        text += f"Target {i+1}: {target:.2f}\n"
    text += f"\nStop-loss Zone: {stop_loss:.2f}"
    return text

def monitor_targets():
    while True:
        signals = load_signals()
        changed = False

        for signal in signals:
            if "hit" not in signal:
                signal["hit"] = []

            if len(signal["hit"]) >= 7 or signal.get("stop_hit"):
                continue

            try:
                coin_id = get_coin_id_from_symbol(signal["coin"])
                entry = signal["entry"]
                stop = signal["stop_loss"]
                targets = signal["targets"]
                message_id = signal["message_id"]

                price_data = cg.get_price(ids=coin_id, vs_currencies='usd')
                price = price_data[coin_id]["usd"]
                now = datetime.utcnow()

                # Target checking
                for i, target in enumerate(targets):
                    if i in signal["hit"] or price < target:
                        continue

                    signal["hit"].append(i)
                    percent = round(((target - entry) / entry) * 100, 2)
                    duration = now - datetime.fromisoformat(signal["posted_at"])
                    duration_str = str(duration).split('.')[0]

                    bot.send_message(
                        CHANNEL_ID,
                        f"""🎯 Target {i+1} hit for {signal["coin"].upper()}
Current Price: {price}
Gain: +{percent}%
Time Taken: {duration_str}""",
                        reply_to_message_id=message_id
                    )
                    changed = True

                # Stop-loss checking
                if not signal.get("stop_hit") and price <= stop:
                    signal["stop_hit"] = True
                    percent = round(((price - entry) / entry) * 100, 2)
                    duration = now - datetime.fromisoformat(signal["posted_at"])
                    duration_str = str(duration).split('.')[0]

                    bot.send_message(
                        CHANNEL_ID,
                        f"""⛔ Stop-loss hit for {signal["coin"].upper()}
Current Price: {price}
Loss: {percent}%
Time Taken: {duration_str}""",
                        reply_to_message_id=message_id
                    )
                    changed = True

            except Exception as e:
                print("Error in monitoring:", e)

        if changed:
            save_signals(signals)

        time.sleep(60)

@bot.message_handler(func=lambda message: True)
def handle_signal(message):
    try:
        parts = message.text.strip().split()
        if len(parts) != 2:
            bot.reply_to(message, "Please send the signal in this format:\nBTC 64123.5")
            return

        coin = parts[0].upper()
        entry = float(parts[1])
        stop_loss = round(entry * (1 - STOP_LOSS_PERCENT / 100), 4)
        targets = [round(entry * (1 + p / 100), 4) for p in TARGET_PERCENTS]

        signal_text = format_signal_text(coin, entry, targets, stop_loss)
        sent = bot.send_message(CHANNEL_ID, signal_text)

        signals = load_signals()
        signals.append({
            "coin": coin,
            "entry": entry,
            "targets": targets,
            "stop_loss": stop_loss,
            "message_id": sent.message_id,
            "posted_at": datetime.utcnow().isoformat(),
            "hit": []
        })
        save_signals(signals)

        bot.reply_to(message, "Signal successfully published.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

# Start monitoring in a background thread
threading.Thread(target=monitor_targets, daemon=True).start()

bot.infinity_polling()
