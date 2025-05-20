import telebot

BOT_TOKEN = '7653756929:AAFVze2LSOW_dw1NhxUTGlPtiQ5VN-mzRao'
CHANNEL_ID = '@Dreamcryptospotsignals'

bot = telebot.TeleBot(BOT_TOKEN)

TARGETS = [1.9, 3.9, 8.6, 18.4, 24.2, 32.3, 40]

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

        signal = f"""#SPOT SIGNAL

Coin: {coin}
Entry Price: {price}
Stop Loss: {stop_loss}

Targets:
1. {targets[0]}
2. {targets[1]}
3. {targets[2]}
4. {targets[3]}
5. {targets[4]}
6. {targets[5]}
7. {targets[6]}

#DreamCryptoSpot
"""

        bot.send_message(message.chat.id, signal)
        bot.send_message(CHANNEL_ID, signal)

    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

bot.polling()