#!/usr/bin/env python3

import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 🧭 Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.analyzer import run_analysis
from utils.symbols import resolve_symbol_alias as resolve_symbol
from formatters.markdown_formatter_discord import format_report_discord

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("DISCORD_CHANNEL_IDS", "").split(",") if cid.strip()]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

def normalize_timeframe(tf: str) -> str:
    tf = tf.lower().replace("min", "m").replace("hour", "h").replace("hr", "h")
    if tf.endswith("m") and tf[:-1].isdigit():
        return f"{tf[:-1]}min"
    elif tf.endswith("h") and tf[:-1].isdigit():
        return f"{tf[:-1]}h"
    elif tf == "daily":
        return "1d"
    return tf

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    # Schedule automatic reports
    scheduler = AsyncIOScheduler()
    trigger = CronTrigger(hour="13,14,17,19", minute=30, day_of_week="mon-fri")  # 9:30, 10:30, 1:30, 3:30 PM ET
    scheduler.add_job(send_scheduled_discord_reports, trigger)
    scheduler.start()

    # Optional boot message
    for channel_id in CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send("✅ KawaiiTrader bot is live and scheduled.")

@bot.command(name="ping")
async def ping(ctx):
    if ctx.channel.id not in CHANNEL_IDS:
        await ctx.send("❌ You can't use this command in this channel.")
        return
    await ctx.send("🏓 Pong! Bot is working.")

@bot.command(name="report")
async def report(ctx, *args):
    if ctx.channel.id not in CHANNEL_IDS:
        await ctx.send("❌ You can't use this command in this channel.")
        return

    if not args:
        await ctx.send("Usage: `!report SYMBOL[,SYMBOL2,...] [TIMEFRAME1[,TIMEFRAME2,...]]`")
        return

    raw_symbols = [arg for arg in args if not any(char.isdigit() for char in arg)]
    raw_timeframes = [arg for arg in args if any(char.isdigit() for char in arg)]

    symbols = [resolve_symbol(sym.strip().upper()) for group in raw_symbols for sym in group.split(",") if sym.strip()]
    timeframes = [normalize_timeframe(tf.strip()) for group in raw_timeframes for tf in group.split(",") if tf.strip()]
    if not symbols:
        await ctx.send("❌ No valid symbols found.")
        return
    if not timeframes:
        timeframes = ['15min']  # Default

    for symbol in symbols:
        for tf in timeframes:
            try:
                name = symbol.get("input_symbol", symbol.get("db_symbol", "???"))
                await ctx.send(f"🌸 Running report for `{name} @ {tf}`...")

                report_obj = run_analysis(symbol_details=symbol, timeframe=tf)
                report_text = format_report_discord(report_obj)

                await ctx.send(report_text)

                if report_obj.chart_path and os.path.exists(report_obj.chart_path):
                    await ctx.send(file=discord.File(report_obj.chart_path))

            except Exception as e:
                await ctx.send(f"❌ Error generating report for {symbol.get('input_symbol')} {tf}: {e}")

@bot.command(name="test_schedule")
async def test_schedule(ctx):
    if ctx.channel.id not in CHANNEL_IDS:
        await ctx.send("❌ You can't use this command in this channel.")
        return
    await ctx.send("🧪 Running scheduled report now...")
    await send_scheduled_discord_reports()

async def send_scheduled_discord_reports():
    symbol = "ES"
    timeframes = ["1min", "5min", "15min", "1h", "4h"]

    for tf in timeframes:
        try:
            resolved = resolve_symbol_alias(symbol)
            report_obj = run_analysis(resolved, tf)
            report_text = format_report_discord(report_obj)
            chart_path = getattr(report_obj, "chart_path", None)

            for channel_id in CHANNEL_IDS:
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(report_text[:2000])
                    if chart_path and os.path.exists(chart_path):
                        await channel.send(file=discord.File(chart_path))

        except Exception as e:
            print(f"❌ Scheduled Discord report failed for {symbol} {tf}: {e}")

bot.run(TOKEN)
