🐣 KawaiiTrader v6

KawaiiTrader is a lightweight market structure and manipulation detection engine designed for futures traders. This version integrates CLI and Telegram bot reporting, powered by historical data from Databento.

🚀 Features

🔍 Price action range detection using body candles
🟨 Manipulation detection based on full-body closes and momentum filters
📐 IRZ Fibonacci projections with directional bias
🔁 Fallback to raw trade data if OHLCV is unavailable
🤖 Telegram bot interface: Get real-time reports from anywhere
🧠 Symbol aliasing (e.g. ES → ES.c.0)
🧼 Clean .env-based key loading, no hardcoded secrets
📦 Installation

git clone https://github.com/yourusername/kawaiitrader.git
cd kawaiitrader
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
🔐 .env Setup

Create a .env file in the project root with your credentials:

DATABENTO_API_KEY=your_db_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
✅ Do NOT commit this file — it’s ignored via .gitignore.
💻 CLI Usage

python3 main.py ES 15min
Default timeframe is 15min if not specified.
💬 Telegram Bot

Start the bot:

source .env
python3 bot/telegram_interface.py
Use in Telegram:

/report ES 1h
/report BTC
📊 Report Contents

Support & Resistance levels
Trendline detection
Consolidation range detection
Manipulation (fakeouts with return)
Breakouts (no return)
IRZ Fibonacci projection with bias and target levels
⚠️ Considerations & Limitations

🔁 Historical data only — no live streaming (by design)
📉 Manipulation logic relies on full candle closes and ATR filters
🔓 API keys must be valid and current in .env
🔁 Telegram bot must be restarted to pick up new .env changes
✅ Ensure only one instance of the bot is running to avoid
Conflict: terminated by other getUpdates request
🧪 Debug Tips

Add print() statements in analyzer.py to trace flow
Use source .env before running CLI or bot
Check .env changes by running:
echo $DATABENTO_API_KEY
📂 Version

v6 — Stable as of May 2025

🧠 License

MIT — use freely with attribution

Let me know when you’re ready to commit this with your v6 Git snapshot.