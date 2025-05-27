import telebot
import json
import os
import time
import threading
from datetime import datetime
from pycoingecko import CoinGeckoAPI
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))

SIGNALS_FILE = 'signals.json'

bot = telebot.TeleBot(TOKEN)
cg = CoinGeckoAPI()

TARGET_PERCENTS = [1.9, 3.9, 8.6, 18.4, 24.2, 32.3, 40.0]
STOP_LOSS_PERCENT = 2

def load_signals():
    if not os.path.exists(SIGNALS_FILE):
        return []
    with open(SIGNALS_FILE, 'r') as f:
        return json.load(f)

def save_signals(signals):
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(signals, f, indent=2)

def format_signal_text(coin, entry, targets, stop_loss):
    text = f"""🚨 New SPOT Signal 🚨

Coin: {coin.upper()}
Entry Zone: {entry}

🎯 Targets:
"""
    for i, target in enumerate(targets):
        text += f"Target {i+1}: {target:.2f}\n"
    text += f"\n⛔ Stop-loss: {stop_loss:.2f}\n"
    text += "\n#DreamCryptoSpot #CryptoSignals"
    return text

def monitor_targets():
    print("Monitoring thread started.")
    while True:
        signals = load_signals()
        changed = False

        for signal in signals:
            if "hit" not in signal:
                signal["hit"] = []

            if len(signal["hit"]) >= 7 or signal.get("stop_hit"):
                continue

            try:
                coin_id = signal["coin"].lower()
                entry = signal["entry"]
                stop = signal["stop_loss"]
                targets = signal["targets"]
                message_id = signal["message_id"]

                price_data = cg.get_price(ids=coin_id, vs_currencies='usd')
                price = price_data[coin_id]["usd"]
                now = datetime.utcnow()

                for i, target in enumerate(targets):
                    if i in signal["hit"] or price < target:
                        continue

                    signal["hit"].append(i)
                    percent = round(((target - entry) / entry) * 100, 2)
                    duration = now - datetime.fromisoformat(signal["posted_at"])
                    duration_str = str(duration).split('.')[0]

                    bot.send_message(
                        CHANNEL_ID,
                        f"""🎯 Target {i+1} hit for {coin_id.upper()}
Current Price: {price}
Profit: +{percent}%
Time elapsed: {duration_str}""",
                        reply_to_message_id=message_id
                    )
                    changed = True

                if not signal.get("stop_hit") and price <= stop:
                    signal["stop_hit"] = True
                    percent = round(((price - entry) / entry) * 100, 2)
                    duration = now - datetime.fromisoformat(signal["posted_at"])
                    duration_str = str(duration).split('.')[0]

                    bot.send_message(
                        CHANNEL_ID,
                        f"""⛔ Stop-loss hit for {coin_id.upper()}
Current Price: {price}
Loss: {percent}%
Time elapsed: {duration_str}""",
                        reply_to_message_id=message_id
                    )
                    changed = True

            except Exception as e:
                print("Error during monitoring:", e)

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

        bot.reply_to(message, "Signal posted successfully.")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

if __name__ == '__main__':
    print("Starting bot with polling...")
    threading.Thread(target=monitor_targets, daemon=True).start()
    bot.infinity_polling()
