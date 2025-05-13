import os
import sys
import discord
from discord.ext import commands
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 🔁 Allow relative imports from project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analyzer import run_analysis
from utils.symbols import resolve_symbol_alias
from formatters.markdown_formatter_discord import format_report_discord

# 🔐 Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_IDS = [int(cid.strip()) for cid in os.getenv("DISCORD_CHANNEL_IDS", "").split(",") if cid.strip()]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 🛑 Scheduler guard to prevent duplication
scheduler_started = False

@bot.event
async def on_ready():
    global scheduler_started

    print(f"✅ KawaiiTrader Discord bot ready as {bot.user}")

    if not scheduler_started:
        scheduler = AsyncIOScheduler()
        trigger = CronTrigger(hour="13,14,17,19", minute=30, day_of_week="mon-fri")  # 9:30, 10:30, 1:30, 3:30 ET
        scheduler.add_job(send_scheduled_discord_reports, trigger)
        scheduler.start()
        scheduler_started = True
        print("📅 Scheduler started.")
    else:
        print("⚠️ Scheduler already started. Skipping duplicate start.")

    for channel_id in DISCORD_CHANNEL_IDS:
        channel = bot.get_channel(channel_id)
        if channel:
            await channel.send("✅ KawaiiTrader bot is live and scheduled.")

@bot.command()
async def report(ctx, symbol: str = "ES", tf: str = "15min"):
    try:
        resolved = resolve_symbol_alias(symbol)
        report = run_analysis(resolved, tf)
        output = format_report_discord(report)

        await ctx.send(output[:2000])

        chart_path = getattr(report, "chart_path", None)
        if chart_path and os.path.exists(chart_path):
            await ctx.send(file=discord.File(chart_path))

    except Exception as e:
        await ctx.send(f"❌ Error generating report for `{symbol} {tf}`: {e}")

@bot.command()
async def test_schedule(ctx):
    await ctx.send("⏳ Running scheduled report now...")
    await send_scheduled_discord_reports()

async def send_scheduled_discord_reports():
    symbol = "ES"
    timeframes = ["1min", "5min", "15min", "1h", "4h"]

    for tf in timeframes:
        try:
            resolved = resolve_symbol_alias(symbol)
            report = run_analysis(resolved, tf)
            output = format_report_discord(report)
            chart_path = getattr(report, "chart_path", None)

            for channel_id in DISCORD_CHANNEL_IDS:
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(output[:2000])
                    if chart_path and os.path.exists(chart_path):
                        await channel.send(file=discord.File(chart_path))

        except Exception as e:
            print(f"❌ Scheduled Discord report failed for {symbol} {tf}: {e}")

# 🚀 Start the bot
bot.run(DISCORD_TOKEN)
