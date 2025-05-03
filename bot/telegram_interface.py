# bot/telegram_interface.py

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from cli.kawaii_cli import run_cli_report

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /report SYMBOL[,SYMBOL2,...] [TIMEFRAME]")
            return
        
        symbols = args[0].split(',')
        timeframe = args[1] if len(args) > 1 else '15min'

        for symbol in symbols:
            result = run_cli_report(symbol, timeframe)
            await update.message.reply_markdown_v2(result)

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("report", report))
    print("Telegram bot is running...")
    app.run_polling()
