from future_admiral_v7.alerts.discord import send_discord
from dotenv import load_dotenv
load_dotenv()
import os

print("Webhook set:", "YES" if os.getenv("DISCORD_WEBHOOK_URL") else "NO")
ok = send_discord("🟢 Future Admiral webhook test — agar yeh dikha to setup sahi hai.")
print("Result:", "OK" if ok else "FAIL")
