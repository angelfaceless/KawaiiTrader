import os
import telegram
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_IDS = [cid.strip() for cid in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if cid.strip()]
BOT = telegram.Bot(token=BOT_TOKEN)

async def send_report_to_telegram(text: str, chart_path: str = None):
    try:
        for chat_id in CHAT_IDS:
            await BOT.send_message(chat_id=chat_id, text=text, parse_mode="MarkdownV2")
            if chart_path and os.path.exists(chart_path):
                with open(chart_path, "rb") as image_file:
                    await BOT.send_photo(chat_id=chat_id, photo=image_file)
    except Exception as e:
        print(f"❌ Telegram send failed: {e}")

