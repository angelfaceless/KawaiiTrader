import sys
from core.analyzer import run_analysis
from formatters.markdown_formatter import format_report_markdown

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
        print("Usage: python3 main.py <symbol(s)> <timeframe(s)>")
        return

    # 🧠 Step 1: Flatten and split on commas
    flat_args = [x.strip() for arg in args for x in arg.split(",") if x.strip()]

    # 🧠 Step 2: Classify into symbols and timeframes
    raw_symbols = []
    raw_timeframes = []
    for item in flat_args:
        cleaned = item.lower()
        if any(char.isdigit() for char in cleaned):  # timeframe
            raw_timeframes.append(item)
        else:
            raw_symbols.append(item)

    symbols = [s.upper() for s in raw_symbols]
    timeframes = [normalize_timeframe(t) for t in raw_timeframes]

    if not symbols or not timeframes:
        print("Error: Please specify both symbol(s) and timeframe(s)")
        return

    for symbol in symbols:
        for timeframe in timeframes:
            print(f"\n[🌸 Running report for: {symbol} @ {timeframe}]")
            try:
                report = run_analysis(symbol, timeframe)
                print(format_report_markdown(report))
            except Exception as e:
                print(f"[ERROR] Failed to analyze {symbol} on {timeframe}: {e}")
