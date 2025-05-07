# main.py

import sys
from cli.kawaii_cli import main as cli_main

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        print("Usage: python3 main.py SYMBOL [TIMEFRAME]")
        print("Example: python3 main.py ES 1h")
        sys.exit(1)

    symbol_arg = args[0]
    tf = args[1] if len(args) > 1 else "15min"

    symbols = [s.strip() for s in symbol_arg.split(",")]
    for symbol in symbols:
        cli_main(symbol, tf)
