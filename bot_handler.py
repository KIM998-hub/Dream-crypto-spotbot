import telebot
import requests

# إعدادات البوت
BOT_TOKEN = '7653756929:AAGnPLi2VY14mmcV5wsKFIOh8C5uvzfYy2s'
CHANNEL_ID = -1002509422719
bot = telebot.TeleBot(BOT_TOKEN)

# النسب
STOP_LOSS_PCT = 0.02
TARGET_PCTS = [0.019, 0.039, 0.086, 0.184, 0.242, 0.323, 0.40]

def get_price(symbol):
    response = requests.get('https://api.coingecko.com/api/v3/simple/price', params={
        'ids': symbol.lower(),
        'vs_currencies': 'usd'
    })
    data = response.json()
    return data.get(symbol.lower(), {}).get('usd', None)

def format_signal(coin, entry, stop_loss, targets):
    target_lines = '\n'.join([f"🎯 الهدف {i+1}: `{t:.4f}`" for i, t in enumerate(targets)])
    return f"""
🚨🚨 توصية جديدة 🚨🚨

📊 العملة: *{coin.upper()}*
💰 السعر الحالي: `{entry:.4f}`
🛡️ وقف الخسارة: `{stop_loss:.4f}`

{target_lines}

📡 *نشر تلقائي بواسطة البوت الذكي*
🔥 بالتوفيق في تداولاتكم يا أبطال!
    """

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    try:
        if '/' not in message.text:
            bot.reply_to(message, "❗ الرجاء إرسال التوصية بهذا الشكل: BTC/USDT")
            return

        symbol = message.text.split('/')[0].strip().lower()
        price = get_price(symbol)

        if price is None:
            bot.reply_to(message, "⚠️ لم أتمكن من جلب سعر العملة. تأكد من كتابة الرمز الصحيح مثل BTC أو ETH.")
            return

        stop_loss = price * (1 - STOP_LOSS_PCT)
        targets = [price * (1 + pct) for pct in TARGET_PCTS]
        text = format_signal(symbol.upper(), price, stop_loss, targets)

        bot.send_message(CHANNEL_ID, text, parse_mode="Markdown")
        bot.reply_to(message, "✅ تم نشر التوصية بنجاح!")

    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

print("🤖 البوت يعمل وينتظر التوصيات...")
bot.polling()
