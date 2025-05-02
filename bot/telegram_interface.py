import os
import sys
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# 🔐 Reset any stale env keys
os.environ.pop("DATABENTO_API_KEY", None)
os.environ.pop("TELEGRAM_BOT_TOKEN", None)

# 📂 Load .env from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path, override=True)

# ✅ Confirm token and key load
print(f"[DEBUG] Loaded TELEGRAM_TOKEN: {os.environ.get('TELEGRAM_BOT_TOKEN')}")
print(f"[DEBUG] Loaded DATABENTO_API_KEY: {os.environ.get('DATABENTO_API_KEY')}")

# 🔧 Add root to path for CLI access
sys.path.append(project_root)

from cli.kawaii_cli import run_analysis


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /report SYMBOL [TIMEFRAME], e.g. /report ES 15m")
        return

    symbol = args[0]
    timeframe = args[1] if len(args) > 1 else "15m"

    try:
        result = run_analysis(symbol, timeframe)
        await update.message.reply_text(result, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in environment")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("report", report))

    print("Telegram bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
