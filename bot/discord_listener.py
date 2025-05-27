import os
import sys
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

# 🔁 Allow relative imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analyzer import run_analysis
from utils.symbols import resolve_symbol_alias as resolve_symbol
from formatters.markdown_formatter_discord import format_report_discord

# 🔐 Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("DISCORD_CHANNEL_IDS", "").split(",") if cid.strip()]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 🛑 Scheduler and ready guard
scheduler = AsyncIOScheduler()
scheduler_started = False
bot_ready_once = False  # ✅ Prevent duplicate startup messages

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
    global scheduler_started, bot_ready_once
    if bot_ready_once:
        return  # ✅ Avoid duplicate announcements
    bot_ready_once = True

    print(f"✅ KawaiiTrader Discord bot ready as {bot.user}")

    if not scheduler_started:
        trigger = CronTrigger(hour="13,14,17,19", minute=30, day_of_week="mon-fri")
        scheduler.add_job(send_scheduled_discord_reports, trigger)
        scheduler.start()
        print("📅 Scheduler started.")
        for job in scheduler.get_jobs():
            print(f"🔔 Job {job.id} next run: {job.next_run_time}")
        scheduler_started = True

    for channel_id in DISCORD_CHANNEL_IDS:
        try:
            channel = await bot.fetch_channel(channel_id)
            if channel:
                await channel.send("✅ KawaiiTrader bot is live and scheduled.")
        except Exception as e:
            print(f"❌ Failed to fetch or send to channel {channel_id}: {e}")

@bot.command()
async def report(ctx, *args):
    if not args:
        await ctx.send("❌ Please specify at least one symbol or timeframe.")
        return

    raw_symbols = [arg for arg in args if not any(char.isdigit() for char in arg)]
    raw_timeframes = [arg for arg in args if any(char.isdigit() for char in arg)]

    symbols = [resolve_symbol(sym.strip().upper()) for group in raw_symbols for sym in group.split(",") if sym.strip()]
    timeframes = [normalize_timeframe(tf.strip()) for group in raw_timeframes for tf in group.split(",") if tf.strip()]

    if not symbols:
        await ctx.send("❌ No valid symbols provided.")
        return
    if not timeframes:
        timeframes = ["15min"]  # default

    # 🌸 Dynamic message
    sym_str = ", ".join(s["input_symbol"] for s in symbols)
    tf_str = ", ".join(timeframes)
    plural = "report" if len(symbols) * len(timeframes) == 1 else "reports"
    await ctx.send(f"🌸 Running {plural} for {sym_str} @ {tf_str}...")

    # ✅ Limit concurrent report processing to reduce memory usage
    semaphore = asyncio.Semaphore(2)

    async def generate_report(symbol, tf):
        async with semaphore:
            try:
                report = await asyncio.to_thread(run_analysis, symbol, tf)
                output = format_report_discord(report)
                chart_path = getattr(report, "chart_path", None)
                return {
                    "symbol": symbol["input_symbol"],
                    "timeframe": tf,
                    "output": output,
                    "chart_path": chart_path,
                    "error": None,
                }
            except Exception as e:
                return {
                    "symbol": symbol["input_symbol"],
                    "timeframe": tf,
                    "output": None,
                    "chart_path": None,
                    "error": str(e),
                }

    tasks = [generate_report(symbol, tf) for symbol in symbols for tf in timeframes]
    results = await asyncio.gather(*tasks)

    for result in results:
        if result["error"]:
            await ctx.send(f"❌ Error generating report for `{result['symbol']} {result['timeframe']}`: {result['error']}")
        else:
            await ctx.send(result["output"][:2000])
            if result["chart_path"] and os.path.exists(result["chart_path"]):
                await ctx.send(file=discord.File(result["chart_path"]))

@bot.command()
async def test_schedule(ctx):
    await ctx.send("⏳ Running scheduled report now...")
    await send_scheduled_discord_reports()

async def send_scheduled_discord_reports():
    print(f"⏰ Scheduled report triggered at {datetime.utcnow()} UTC")
    symbol = "ES"
    timeframes = ["1min", "5min", "15min", "1h", "4h"]

    for tf in timeframes:
        try:
            resolved = resolve_symbol(symbol)
            print(f"🔍 Running analysis for {resolved['input_symbol']} {tf}")
            report = await asyncio.to_thread(run_analysis, resolved, tf)
            output = format_report_discord(report)
            chart_path = getattr(report, "chart_path", None)

            for channel_id in DISCORD_CHANNEL_IDS:
                try:
                    channel = await bot.fetch_channel(channel_id)
                    if channel:
                        print(f"📤 Sending to channel {channel_id}")
                        await channel.send(output[:2000])
                        if chart_path and os.path.exists(chart_path):
                            await channel.send(file=discord.File(chart_path))
                except Exception as e:
                    print(f"❌ Failed to send to channel {channel_id}: {e}")

        except Exception as e:
            print(f"❌ Scheduled Discord report failed for {symbol} {tf}: {e}")

# 🚀 Start the bot
bot.run(DISCORD_TOKEN)
