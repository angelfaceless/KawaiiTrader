# cli/kawaii_cli.py

import sys
from core.analyzer import run_analysis
from utils.symbols import resolve_symbol_alias


def main(symbol=None, timeframe="15min"):
    # Allow command-line fallback if not passed in
    if symbol is None:
        if len(sys.argv) < 2:
            print("Usage: python main.py <SYMBOL> [TIMEFRAME]")
            sys.exit(1)
        symbol = sys.argv[1]
        timeframe = sys.argv[2] if len(sys.argv) > 2 else "15min"

    mapped_symbol = resolve_symbol_alias(symbol)
    print(f"[KawaiiTrader] Running report for: ['{symbol}', '{timeframe}'] @ {timeframe}")

    try:
        result = run_analysis(mapped_symbol, timeframe)
        print(result)
    except Exception as e:
        print(f"[ERROR] Failed to analyze {mapped_symbol} on {timeframe}: {e}")
