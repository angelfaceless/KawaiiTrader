# kawaiitrader/cli/kawaii_cli.py

import argparse
from dotenv import load_dotenv
from core.analyzer import run_analysis

load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Run kawaiitrader reporting bot.")
    parser.add_argument("symbols", nargs="*", help="Asset symbols like ES, NQ, BTC")
    parser.add_argument("--tf", "--timeframe", dest="timeframe", default="1h", help="Timeframe (e.g., 15m, 1h)")

    args = parser.parse_args()
    symbols = args.symbols or ["ES"]

    print(f"[KawaiiTrader] Running report for: {symbols} @ {args.timeframe}")

    for symbol in symbols:
        print(f" - Generating report for {symbol} on {args.timeframe}")
        try:
            report = run_analysis(symbol, args.timeframe)
            print("\n" + report + "\n")
        except Exception as e:
            print(f"[ERROR] Failed to generate report for {symbol}: {e}")
