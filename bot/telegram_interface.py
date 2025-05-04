import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from core.analyzer import run_analysis
from utils.symbols import resolve_symbol_alias as resolve_symbol
from formatters.markdown_formatter import format_report_markdown

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /report SYMBOL[,SYMBOL2,...] [TIMEFRAME1[,TIMEFRAME2,...]]")
            return

        # Symbols (comma-separated)
        raw_symbols = args[0].split(',')
        symbols = [resolve_symbol(sym.strip()) for sym in raw_symbols]

        # Timeframes (comma/space-tolerant)
        timeframes = ['15min']  # default
        if len(args) > 1:
            raw_tf = " ".join(args[1:])  # allow "15min, 1h"
            timeframes = [tf.strip() for tf in raw_tf.split(',') if tf.strip()]

        # Loop through each symbol + timeframe combo
        for symbol in symbols:
            for tf in timeframes:
                report = run_analysis(symbol, tf)
                report_text = format_report_markdown(report)

                await update.message.reply_markdown_v2(report_text)

                with open(report.chart_path, "rb") as chart_file:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=chart_file)

    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

if __name__ == "__main__":
    if not asyncio.get_event_loop_policy().get_event_loop().is_running():
        asyncio.set_event_loop(asyncio.new_event_loop())

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("report", report))
    print("Telegram bot is running...")
    app.run_polling()
