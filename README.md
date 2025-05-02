# 🌸 KawaiiTrader — Market Structure & Manipulation Detection Bot

KawaiiTrader is an automated futures market structure analysis engine that fetches continuous futures data from **Databento** and identifies support/resistance, trendlines, manipulation wicks, and IRZ retracement zones.

It supports flexible timeframes (`15min`, `1h`, `3h`, etc.) and generates both CLI and **Telegram Bot** reports in beautiful Markdown.

---

## ✨ Features

- 🔁 Continuous futures symbol support (e.g. `ES.c.0`)
- ⏱ Dynamic timeframe support (`15min`, `1h`, `3h`, `6h`, `1d`)
- 📉 Support and Resistance level detection
- 📈 Trendline analysis with multi-window pivot scanning
- 🟥 Manipulation wick detection and return-to-range logic
- 📊 IRZ (Impulse Retrace Zones) Fibonacci-based projections
- 💬 Telegram bot `/report SYMBOL TIMEFRAME` support
- 🧠 Automatically adjusts for Databento historical data latency
- 🕒 Dynamic candle lookback: fetches minimum 50 bars based on timeframe
- 🪷 Beautiful CLI and Telegram output with Markdown formatting

---

## ⚙️ Installation

```bash
git clone https://github.com/your-username/kawaiitrader.git
cd kawaiitrader

# Create .env with your Databento key
echo 'DATABENTO_API_KEY=db-xxxxxxx' > .env

# Install dependencies
pip install -r requirements.txt
🚀 CLI Usage

# Run analysis from terminal
python3 main.py ES 15min
python3 main.py NQ 1h
python3 main.py BTC 3h
ES → auto-mapped to ES.c.0
Default report format is printed in Markdown.
💬 Telegram Bot Setup

Create a bot and get the token
Set the token as an env variable:
export TELEGRAM_BOT_TOKEN=your_token_here
Run the bot:
PYTHONPATH=$(pwd) python3 -m bot.telegram_interface
Send commands in chat:
/report ES 15min
/report NQ 1h
/report BTC 3h
📝 Supports auto symbol mapping (e.g. ES → ES.c.0)

📒 Limitations

Only symbols with Databento continuous mappings will work.
Telegram bot uses polling — don’t run more than one instance.
Historical data may have ~10 minute latency. Live alerts not implemented yet.
Minimum of 50 candles required for valid analysis.
📅 Planned

Live data alert support via WebSocket + cron
Web UI with trendline & range visualization
TradingView webhook ingestion
Multi-symbol scheduling via cron.yaml or Supabase tasks
🔐 Security

Ensure .env is in your .gitignore. Never push your API keys or bot tokens publicly.

📎 Example Output

📊 KawaiiTrader Report for ES.c.0 (15min)
========================================
Fetched 184 candles from Databento

🟦 Support Levels: [...]
🟥 Resistance Levels: [...]
🟩 Support trendline detected (15min)

🟥 Range (body-only) over last 50 bars: 4450 – 4620
🟨 Manipulation Detected: Price wicked above and returned inside range.
🟪 IRZ Levels (projected downward):
Retrace Zone → 4570 / 4585 / 4600
Profit Targets → 4400 / 4340 / 4280
