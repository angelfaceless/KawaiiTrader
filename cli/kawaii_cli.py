import sys
from core.analyzer import run_analysis
from formatters.markdown_formatter import format_report_markdown
from utils.symbols import resolve_symbol_alias

def normalize_timeframe(tf: str) -> str:
    """Normalize user input timeframes like 5m, 1hr to system format."""
    tf = tf.lower().replace(" ", "")
    replacements = {
        "m": "min",
        "hr": "h",
        "h": "h",
        "d": "d"
    }

    for key, val in replacements.items():
        if tf.endswith(key):
            number = tf[:-len(key)]
            if number.isdigit():
                return f"{number}{val}"
    return tf

def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: python3 kawaii_cli.py <symbol(s)> <timeframe(s)>")
        print("Example: python3 kawaii_cli.py ES,AAPL 15min,1d")
        return

    flat_args = [x.strip() for arg in args for x in arg.split(",") if x.strip()]

    raw_symbols = []
    raw_timeframes = []
    for item in flat_args:
        cleaned = item.lower()
        # A simple check if it contains a digit or is a known timeframe string
        if any(char.isdigit() for char in cleaned) or cleaned in ["1d", "1w", "1month", "d", "w", "month", "min", "h", "hr"]:
            raw_timeframes.append(item)
        else:
            raw_symbols.append(item)

    symbols = [s.upper() for s in raw_symbols]
    timeframes = [normalize_timeframe(t) for t in raw_timeframes]

    if not symbols or not timeframes:
        print("Error: Please specify both symbol(s) and timeframe(s)")
        return

    for symbol_input in symbols:
        for timeframe in timeframes:
            print(f"\n[🌸 Running report for: {symbol_input} @ {timeframe}]")
            
            symbol_details = resolve_symbol_alias(symbol_input)
            
            try:
                report = run_analysis(symbol_details, timeframe)
                print(format_report_markdown(report))
            except Exception as e:
                db_symbol_for_error = symbol_details.get("db_symbol", symbol_details.get("symbol", symbol_input))
                print(f"[ERROR] Failed to analyze {db_symbol_for_error} (input: {symbol_input}) on {timeframe}: {e}")

if __name__ == "__main__":
    main()
