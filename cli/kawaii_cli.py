import sys
from core.analyzer import run_analysis
from formatters.markdown_formatter import format_report_markdown

def main():
    args = sys.argv[1:]

    if not args:
        print("Usage: python3 main.py <symbol(s)> <timeframe(s)>")
        return

    symbols = [arg for arg in args if not any(char.isdigit() for char in arg)]
    timeframes = [arg for arg in args if any(char.isdigit() for char in arg)]

    if not symbols or not timeframes:
        print("Error: Please specify both symbol(s) and timeframe(s)")
        return

    for symbol in symbols:
        for timeframe in timeframes:
            print(f"\n[🟪 Running report for: {symbol} @ {timeframe}]")
            try:
                report = run_analysis(symbol, timeframe)
                print(format_report_markdown(report))
            except Exception as e:
                print(f"[ERROR] Failed to analyze {symbol} on {timeframe}: {e}")
