#!/usr/bin/env python3

import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Import CLI logic for symbol mapping and reporting
from main import map_to_continuous, run_single_report

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Default timeframe if none provided
DEFAULT_TF = "15min"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🌸 Welcome to KawaiiTrader! Use /report <symbol> [<timeframe>] 🌸")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Usage: /report <symbol> [<timeframe>]")
        return

    raw_symbol = args[0].upper()
    timeframe = args[1] if len(args) > 1 else DEFAULT_TF

    try:
        mapped_symbol = map_to_continuous(raw_symbol)
        logger.info(f"[TelegramBot] Mapped {raw_symbol} to {mapped_symbol} with tf={timeframe}")
        await update.message.reply_text(f"🌸 Generating report for {mapped_symbol} on {timeframe}... 🌸")

        result = run_single_report(mapped_symbol, timeframe)

        if result:
            await update.message.reply_text(result)
        else:
            await update.message.reply_text(f"⚠️ No report generated for {mapped_symbol}.")
    except Exception as e:
        logger.exception("[TelegramBot] Error in /report command")
        await update.message.reply_text(f"⚠️ Error: {e}")

def main():
    print("🐞 DEBUG: main() is running...")

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("⚠️ TELEGRAM_BOT_TOKEN environment variable not set.")
        return

    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("report", report))

    print("🌸 [TelegramBot] KawaiiTrader Bot is running and polling Telegram... 🌸")
    application.run_polling()

if __name__ == "__main__":
    main()
