import os
import argparse
from dotenv import load_dotenv
import databento as db
import pandas as pd
from datetime import datetime

# Month code map (CME)
MONTH_CODES = {
    "F": 1, "G": 2, "H": 3, "J": 4,
    "K": 5, "M": 6, "N": 7, "Q": 8,
    "U": 9, "V": 10, "X": 11, "Z": 12,
}

def parse_contract_date(symbol: str) -> datetime | None:
    try:
        root = symbol[:-2]
        code = symbol[-2]
        year_digit = symbol[-1]
        month = MONTH_CODES.get(code)
        if month is None:
            return None
        current_year = datetime.utcnow().year
        decade = current_year - current_year % 10
        year = decade + int(year_digit)
        if year < current_year:
            year += 10
        return datetime(year, month, 1)
    except:
        return None

# Load .env
load_dotenv()
api_key = os.getenv("DATABENTO_API_KEY")
if not api_key:
    raise ValueError("Missing DATABENTO_API_KEY in .env or environment")

# CLI
parser = argparse.ArgumentParser(description="Fetch CME contracts from Databento")
parser.add_argument('--symbol', type=str, help="Symbol root (e.g., ES, NQ, CL)", default=None)
parser.add_argument('--active-only', action='store_true', help="Show only nearest valid contract")
args = parser.parse_args()

print("📡 Fetching Databento contract definitions...")

# Init client
client = db.Historical(key=api_key)

# Fetch data
try:
    data = client.timeseries.get_range(
        dataset="GLBX.MDP3",
        schema="definition",
        symbols="ALL_SYMBOLS",
        start="2024-07-08",
        end="2024-07-09"
    )
except Exception as e:
    print("❌ Failed to fetch from Databento:", e)
    exit(1)

df = data.to_df()
df = df[df["raw_symbol"].notnull()][["raw_symbol", "instrument_id", "ts_event"]].copy()

if args.symbol:
    df = df[df["raw_symbol"].str.startswith(args.symbol.upper())]
    print(f"🔍 Filtering for symbol root: {args.symbol.upper()}")

df["parsed_date"] = df["raw_symbol"].apply(parse_contract_date)
df = df[df["parsed_date"].notnull()]

if df.empty:
    print("⚠️ No matching contracts found.")
    exit(0)

if args.active_only:
    now = datetime.utcnow()
    df = df[df["parsed_date"] >= now.replace(day=1)].sort_values("parsed_date")
    df = df.head(1)
    print("🎯 Most current active contract selected.")

# Save and show
df = df.sort_values("parsed_date")
df.to_csv("contracts.csv", index=False)
print(f"✅ Saved {len(df)} contract(s) to contracts.csv")
print(df[["raw_symbol", "parsed_date"]].to_string(index=False))
