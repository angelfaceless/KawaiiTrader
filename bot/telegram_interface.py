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

        # ✅ Split args into symbols and timeframes cleanly
        raw_symbols = [arg for arg in args if not any(char.isdigit() for char in arg)]
        raw_timeframes = [arg for arg in args if any(char.isdigit() for char in arg)]

        symbols = [resolve_symbol(sym.strip().upper()) for group in raw_symbols for sym in group.split(",") if sym.strip()]
        timeframes = [tf.strip() for group in raw_timeframes for tf in group.split(",") if tf.strip()]

        if not symbols:
            await update.message.reply_text("❌ No valid symbols found.")
            return
        if not timeframes:
            timeframes = ['15min']  # default

        for symbol in symbols:
            for tf in timeframes:
                await update.message.reply_text(f"🌸 Running report for *{symbol}* @ `{tf}`...", parse_mode="Markdown")

                report_obj = run_analysis(symbol, tf)
                report_text = format_report_markdown(report_obj)

                await update.message.reply_markdown_v2(report_text)

                with open(report_obj.chart_path, "rb") as chart_file:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=chart_file)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

if __name__ == "__main__":
    if not asyncio.get_event_loop_policy().get_event_loop().is_running():
        asyncio.set_event_loop(asyncio.new_event_loop())

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("report", report))
    print("Telegram bot is running...")
    app.run_polling()
