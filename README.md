# 🦄 KawaiiTrader

**KawaiiTrader** is a lightweight CLI-based market structure analysis tool for futures contracts (like `ES`, `NQ`, `BTC`) powered by the [Databento API](https://databento.com). It detects support/resistance levels, trendlines, price manipulation, and generates IRZ Fibonacci levels from raw historical market data.

---

## 🚀 Features

- 🔍 Pulls historical futures data using Databento `trades` schema (low-bandwidth, fast)
- 📉 Detects:
  - Support & resistance
  - Trendlines
  - Manipulation wicks
  - Range breakouts
- 🎯 Computes IRZ zones and profit targets
- 🧠 CLI support for flexible inputs
- 💾 Exports symbol lists to CSV
- ✅ Stable on `ES.c.0` 15min reporting as of `v2-trades-schema-stable`

---

## 📦 Requirements

Make sure the following are installed:

- Python 3.10+
- A [Databento API Key](https://databento.com/account/api-keys)
- CME Globex MDP 3 entitlement (Usage-Based or higher)
- 2+ days of data required for accurate trend detection
- UNIX-based system (Mac/Linux)

---

## ⚙️ Installation

```bash
git clone https://github.com/YOUR_USERNAME/kawaiitrader.git
cd kawaiitrader

# (optional) Use a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
Set up your API key in a .env file:

DATABENTO_API_KEY=your_api_key_here
🧠 CLI Usage

▶️ Run a Report
python3 main.py ES.c.0 --tf 15min
ES.c.0: Continuous ES contract with roll rule c, rank 0 (most current)
--tf: Timeframe (supports 1min, 5min, 15min, 1h, etc.)
▶️ Filter & Export All Symbols
python3 list_symbols.py --filter ES
Will generate a contracts.csv of filtered contracts.

🧪 Limitations


Constraint	Description
🔄 Data Latency	Historical API lags ~5–15 minutes from real-time. Avoid querying the future.
🕒 Minimum Lookback	Requires at least 50 bars to perform structural analysis.
⛔️ Symbol Support	Symbol format must match valid Databento continuous format like ES.c.0.
💾 API Plan	Requires CME Globex MDP 3 usage-based access or better.
📊 Schema Used	trades schema (lightweight, includes timestamps & volume).
