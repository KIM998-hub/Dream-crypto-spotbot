import json
import time
import requests
import threading
from datetime import datetime
import telebot

# ✅ إعدادات البوت والقناة
TOKEN = "7653756929:AAGnPLi2VY14mmcV5wsKFIOh8C5uvzfYy2s"
CHANNEL_ID = -1002509422719
SIGNALS_FILE = "signals.json"

bot = telebot.TeleBot(TOKEN)
symbol_to_id_cache = {}

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
        return res.json()[symbol]["usdt"]
    except Exception as e:
        print(f"❌ خطأ في get_price لـ {symbol}: {e}")
        return None

def coin_symbol_to_id(coin):
    coin = coin.lower()
    if coin in symbol_to_id_cache:
        return symbol_to_id_cache[coin]
    try:
        url = "https://api.coingecko.com/api/v3/coins/list"
        response = requests.get(url)
        time.sleep(1.5)
        data = response.json()
        for item in data:
            if item["symbol"] == coin:
                symbol_to_id_cache[coin] = item["id"]
                return item["id"]
        print(f"❌ لم يتم إيجاد Coin ID لـ {coin}")
    except Exception as e:
        print(f"❌ CoinGecko Error: {e}")
    return None

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
                continue

            price = get_price(coin_id)
            if not price:
                continue

            entry = signal["entry"]
            now = time.time()
            elapsed = now - signal["start_time"]
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)

            def send_hit(msg):
                bot.send_message(CHANNEL_ID, msg, reply_to_message_id=signal["msg_id"], parse_mode="Markdown")
                time.sleep(1.5)

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

# تشغيل المراقبة
monitor_targets()
