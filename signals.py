def generate_signal(coin: str, entry: float) -> str:
    stop_loss = round(entry * 0.98, 6)
    percentages = [1.9, 3.9, 8.6, 18.4, 24.2, 32.3, 40]
    targets = [round(entry * (1 + p / 100), 6) for p in percentages]

    message = f"**{coin} SPOT SIGNAL**\n"
    message += f"Entry: `{entry}`\n"
    message += f"Stop-loss: `{stop_loss}`\n"
    for i, target in enumerate(targets):
        message += f"Target {i+1}: `{target}`\n"
    return message

# ----------- استخدام السكربت -----------

text = input("اكتب التوصية (مثل LTOUSDT 0.0507): ").strip()
parts = text.split()

if len(parts) == 2:
    coin = parts[0].upper()
    try:
        entry = float(parts[1])
        print("\nالرسالة الجاهزة للنشر:\n")
        print(generate_signal(coin, entry))
    except ValueError:
        print("تأكد من كتابة السعر بشكل صحيح.")
else:
    print("اكتب التوصية بهذا الشكل: LTOUSDT 0.0507")