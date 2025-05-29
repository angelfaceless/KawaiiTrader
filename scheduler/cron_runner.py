#!/usr/bin/env python3

import sys
import os
import asyncio
import telegram
from dotenv import load_dotenv
from datetime import datetime

# 📁 Enable relative imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analyzer import run_analysis
from utils.symbols import resolve_symbol_alias as resolve_symbol
from formatters.markdown_formatter import format_report_markdown

# 🧪 Load environment variables
load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_ids = [cid.strip() for cid in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if cid.strip()]
bot = telegram.Bot(token=bot_token)

async def run_scheduled_reports():
    symbol = "ES"
    timeframes = ["1min", "5min", "15min", "1h", "4h"]

    for tf in timeframes:
        try:
            resolved = resolve_symbol(symbol)

            # 🧠 Async-safe run_analysis
            report = await asyncio.to_thread(run_analysis, resolved, tf)

            # 👇 Prevent MarkdownV2-style escaping
            output = format_report_markdown(report, escape=False)
            chart_path = getattr(report, "chart_path", None)

            print(f"\n[{symbol} @ {tf}]\n{output}")

            for cid in chat_ids:
                # 📨 Send text report with classic Markdown
                await bot.send_message(
                    chat_id=cid,
                    text=f"[{symbol} @ {tf}]\n{output}",
                    parse_mode=telegram.constants.ParseMode.MARKDOWN
                )

                # 🖼 Send chart image if available
                if chart_path and os.path.exists(chart_path):
                    with open(chart_path, "rb") as img:
                        await bot.send_photo(chat_id=cid, photo=img)

        except Exception as e:
            error_msg = f"❌ Failed to generate or send report for {symbol} {tf}: {e}"
            print(error_msg)
            for cid in chat_ids:
                await bot.send_message(chat_id=cid, text=error_msg)

if __name__ == "__main__":
    asyncio.run(run_scheduled_reports())
