from flask import Flask, request
import telebot
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

API_TOKEN = '7653756929:AAFVze2LSOW_dw1NhxUTGlPtiQ5VN-mzRao'
CHANNEL_ID = '-1002509422719'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

TARGET_PERCENTS = [1.9, 3.9, 8.6, 18.4, 24.2, 32.3, 40.0]
STOP_LOSS_PERCENT = 2.0

def format_price(p):
    return f"{round(p, 4)}"

def get_coin_data(symbol):
    url = "https://api.coingecko.com/api/v3/coins/list"
    coins = requests.get(url).json()
    coin = next((c for c in coins if c['symbol'].lower() == symbol.lower()), None)
    if not coin:
        return None
    coin_id = coin['id']
    coin_info = requests.get(f"https://api.coingecko.com/api/v3/coins/{coin_id}").json()
    return {
        "name": coin_info['name'],
        "logo": coin_info['image']['large']
    }

def generate_image(coin_name, logo_url, entry_price, stop_loss):
    W, H = (800, 300)
    image = Image.new("RGB", (W, H), "#0d1117")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    draw.text((20, 20), f"DreamCryptoSpot Signal", font=title_font, fill="#ffffff")
    draw.text((20, 90), f"Coin: {coin_name}", font=font, fill="#f2a900")
    draw.text((20, 150), f"Entry: {entry_price}", font=font, fill="#00ffcc")
    draw.text((20, 200), f"Stop Loss: {stop_loss}", font=font, fill="#ff4c4c")
    try:
        logo = Image.open(BytesIO(requests.get(logo_url).content)).convert("RGBA")
        logo = logo.resize((80, 80))
        image.paste(logo, (700, 30), logo)
    except:
        pass
    output = BytesIO()
    image.save(output, format='PNG')
    output.seek(0)
    return output

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        parts = message.text.split()
        if len(parts) != 2:
            bot.reply_to(message, "Please send in format: COIN PRICE")
            return
        coin = parts[0].upper()
        entry = float(parts[1])
        stop_loss = round(entry * (1 - STOP_LOSS_PERCENT / 100), 4)
        targets = [round(entry * (1 + p / 100), 4) for p in TARGET_PERCENTS]
        coin_data = get_coin_data(coin)
        if not coin_data:
            bot.reply_to(message, f"Coin {coin} not found on CoinGecko.")
            return
        img = generate_image(coin_data['name'], coin_data['logo'], format_price(entry), format_price(stop_loss))
        bot.send_photo(CHANNEL_ID, img)
        text = f"""<b>🔥 🚨 NEW SPOT SIGNAL 🚨 🔥</b>

<b>🪙 Coin:</b> <code>{coin}</code>
<b>🎯 Entry Price:</b> <code>{format_price(entry)}</code>
<b>🛑 Stop Loss:</b> <code>{format_price(stop_loss)}</code>

<b>🎯 Target Levels:</b>
""" + '\n'.join([f"➤ <code>{format_price(t)}</code>" for t in targets]) + """

#DreamCryptoSpot #CryptoSignals"""
        bot.send_message(CHANNEL_ID, text, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")

@app.rimport telebot
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

# Fetch all CoinGecko coins once
def fetch_coin_list():
    url = 'https://api.coingecko.com/api/v3/coins/list'
    response = requests.get(url)
    if response.status_code == 200:
        return {coin['symbol'].upper(): coin['id'] for coin in response.json()}
    return {}

COIN_LIST = fetch_coin_list()

# Fetch current price
def get_price(coin_id):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get(coin_id, {}).get('usd', None)
    return None

# Monitor prices and send alerts
def monitor_prices():
    while True:
        signals = load_signals()
        updated = False
        for signal in signals:
            if signal["hit_stop"] or len(signal["hit_targets"]) == len(signal["targets"]):
                continue

            coin_id = signal["coin_id"]
            current_price = get_price(coin_id)
            print(f"[{datetime.now()}] {signal['coin']} price: {current_price}")
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

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

# Start monitoring and bot polling
start_monitoring()
bot.infinity_polling()
