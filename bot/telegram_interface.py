import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from core.analyzer import run_analysis
from utils.symbols import resolve_symbol_alias as resolve_symbol
from formatters.markdown_formatter import format_report_markdown

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def normalize_timeframe(tf: str) -> str:
    tf = tf.lower().replace("min", "m").replace("hour", "h").replace("hr", "h")
    if tf.endswith("m") and tf[:-1].isdigit():
        return f"{tf[:-1]}min"
    elif tf.endswith("h") and tf[:-1].isdigit():
        return f"{tf[:-1]}h"
    elif tf == "daily":
        return "1d"
    return tf

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /report SYMBOL[,SYMBOL2,...] [TIMEFRAME1[,TIMEFRAME2,...]]")
            return

        raw_symbols = [arg for arg in args if not any(char.isdigit() for char in arg)]
        raw_timeframes = [arg for arg in args if any(char.isdigit() for char in arg)]

        symbols = [resolve_symbol(sym.strip().upper()) for group in raw_symbols for sym in group.split(",") if sym.strip()]
        timeframes = [normalize_timeframe(tf.strip()) for group in raw_timeframes for tf in group.split(",") if tf.strip()]

        if not symbols:
            await update.message.reply_text("❌ No valid symbols found.")
            return
        if not timeframes:
            timeframes = ['15min']  # default

        for symbol in symbols:
            for tf in timeframes:
                await update.message.reply_text(
                    f"🌸 Running report for *{symbol.get('input_symbol', symbol.get('db_symbol', '???'))}* @ `{tf}`...",
                    parse_mode="Markdown"
                )

                report_obj = run_analysis(symbol_details=symbol, timeframe=tf)
                report_text = format_report_markdown(report_obj)

                await update.message.reply_markdown_v2(report_text)

                with open(report_obj.chart_path, "rb") as chart_file:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=chart_file)

                # 🧠 Dynamic next timeframe suggestion
                next_tf_map = {
                    "1min": "5min", 
                    "5min": "15min",
                    "15min": "1h",
                    "1h": "4h",
                    "4h": "1d",
                    "1d": "1w",
                    "1w": "1mo",
                    "1mo": "1mo"
                }
                suggested_tf = next_tf_map.get(tf, "1h")
                keyboard = [[f"/report {symbol.get('input_symbol')} {suggested_tf}"]]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
                await update.message.reply_text("Done! Tap below for the next timeframe:", reply_markup=reply_markup)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

if __name__ == "__main__":
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("report", report))
    print("Telegram bot is running...")
    app.run_polling()
