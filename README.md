✅ Full README.md
# 📈 KawaiiTrader

KawaiiTrader is a high-performance, price-action-driven technical analysis engine for futures traders. It detects market structure, support/resistance, trendlines, manipulation zones, and Fibonacci IRZ targets. Built to run from both the command line and a real-time Telegram bot.

---

## 🚀 Features

- ✅ Hybrid range detection with ATR filtering
- ✅ Automatic support & resistance mapping
- ✅ Trendline detection using pivots
- ✅ Manipulation detection via wick traps
- ✅ Fibonacci IRZ projection (retracements & targets)
- ✅ Chart visualizations with custom styling
- ✅ CLI and Telegram Bot integration
- ✅ Symbol aliasing (e.g., `BTC` → `BTCK5`)

---

## 🛠 Installation

### 1. Clone the Repo

```bash
git clone https://github.com/angelfaceless/KawaiiTrader.git
cd KawaiiTrader
2. Create Environment and Install Dependencies
Use the helper script:

chmod +x setup.sh
./setup.sh
Or do it manually:

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
3. Create a .env File
cp .env.example .env
Then fill in your API keys:

DATABENTO_API_KEY=your_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
📟 CLI Usage

You can run KawaiiTrader from the command line:

python3 main.py SYMBOL [TIMEFRAME]
Example:
python3 main.py ES 15min
python3 main.py BTC 4h
Default timeframe: 15min
Output includes support/resistance, trendline summary, manipulation zones, IRZ, and a saved chart in /Charts.
🤖 Telegram Bot Usage

1. Start the bot:
python3 bot/telegram_interface.py
Or inside tmux (recommended):

tmux new -s kawaiibot 'source .venv/bin/activate && python3 bot/telegram_interface.py'
2. Interact with it in Telegram:
Format:

/report SYMBOL[,SYMBOL2,...] [TIMEFRAME]
Examples:
/report ES 15min
/report BTC 4h
/report NQ,GC,CL 1h
Output:
Full markdown-formatted report
Inline chart image with Fibs, trendlines, SR, and zones
🧠 Symbol Aliasing

Aliases are automatically resolved:

Alias	Resolved Symbol
BTC	BTCK5 (or current front-month)
ES	ES.c.0
NQ	MNQ.c.0
GC	MGC.c.0
CL	MCL.c.0
🧾 Project Structure

/bot
  telegram_interface.py   ← Telegram bot entry
/cli
  kawaii_cli.py           ← CLI runner
/core
  analyzer.py             ← Main analysis engine
  support_resistance.py   ← S/R detection
  trendline_detector.py   ← Trendline pivots
  manipulation_detector.py← Wick trap logic
  irz_fib.py              ← Fibonacci projection
  visualizer.py           ← Chart rendering
/utils
  symbols.py              ← Symbol aliases
  databento_client.py     ← API data fetching
/formatters
  markdown_formatter.py   ← Markdown report formatting
main.py                   ← CLI entry point
requirements.txt
.env.example
💡 Tips

Use tmux or pm2 to keep your bot running in the background.
All charts are saved in Charts/.
Symbol and timeframe defaults are managed automatically.
Markdown output is Telegram-safe with emojis and proper escaping.
🏁 Roadmap Ideas

Auto-trading with broker API
Scheduler for regular reports
Cloud chart hosting
HTML-based web dashboard
Signal confirmation logic
🔒 Security

.env is gitignored by default. Make sure your tokens are never committed. Run:

git rm --cached .env
If you ever accidentally committed secrets.

🧑‍💻 Author

Made with ♥ by angelfaceless

