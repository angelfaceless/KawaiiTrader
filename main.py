import argparse
from cli.kawaii_cli import main as cli_main
from core.analyzer import run_analysis

# Mapping for continuous contracts
def map_to_continuous(symbol: str) -> str:
    """Map short symbols like ES, NQ, BTC to their continuous Databento symbol format."""
    return f"{symbol.upper()}.c.0"

# Single report entrypoint for external integrations (e.g., Telegram bot)
def run_single_report(symbol: str, timeframe: str = "15min") -> str:
    print(f"[Analyzer] Fetching data for {symbol} on {timeframe} timeframe")
    try:
        return run_analysis(symbol, timeframe)
    except Exception as e:
        return f"[ERROR] Failed to generate report for {symbol}: {e}"

# CLI entrypoint
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KawaiiTrader CLI")
    parser.add_argument("symbols", nargs="+", help="Symbol(s) to analyze, e.g., ES, NQ, BTC")
    parser.add_argument("--tf", "--timeframe", dest="timeframe", default="15min", help="Timeframe (default: 15min)")

    args = parser.parse_args()
    raw_symbols = args.symbols
    timeframe = args.timeframe

    print(f"[KawaiiTrader] Running report for: {raw_symbols} @ {timeframe}")
    for raw_symbol in raw_symbols:
        full_symbol = map_to_continuous(raw_symbol)
        print(f" - Generating report for {full_symbol} on {timeframe}")
        result = run_single_report(full_symbol, timeframe)
        print(result)
