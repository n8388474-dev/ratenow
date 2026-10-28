import os, json, urllib.request, urllib.parse

tok = os.environ.get("TELEGRAM_BOT_TOKEN")
chat = os.environ.get("TELEGRAM_CHAT_ID")
if not tok or not chat:
    raise SystemExit("telegram secrets not set - skipping")
text = json.load(open("data/summary.json", encoding="utf-8"))["text"]
data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
try:
    urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", data, timeout=30)
    print("telegram sent")
except Exception as e:
    print("telegram failed (not critical):", e)
