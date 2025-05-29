import os
import sys
import pandas as pd
import json
import holidays
from datetime import datetime, timedelta, time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.analyzer import run_analysis
from utils.symbols import resolve_symbol_alias
from data.databento_client import fetch_ohlcv, get_dynamic_lookback
from collections import Counter

OUTPUT_FILE = "backtest_results.jsonl"
us_holidays = holidays.US()

# 🕒 Scan only at specific times
SCAN_TIMES = [time(9, 30), time(10, 30), time(13, 30), time(15, 30)]


def monitor_irz_outcomes(df, irz_data, fib_data, direction):
    result = {
        "timestamp": irz_data.get("start_time"),
        "direction": direction,
        "irz_zone": irz_data.get("retracement_zone"),
        "targets_hit": [],
        "max_move_after_draw": 0.0,
    }

    if not fib_data:
        return result

    irz_low, irz_high = irz_data["retracement_zone"]
    fib_targets = fib_data.get("targets", [])
    fib_start_index = irz_data.get("start_index", 0)
    forward_df = df.iloc[fib_start_index + 1:].copy()
    prices = forward_df["close"].values

    max_move = 0.0
    for target in fib_targets:
        target_price = target["price"]
        hit = any(
            price <= target_price if direction == "down" else price >= target_price
            for price in prices
        )
        if hit:
            result["targets_hit"].append(target["level"])

        distance = abs(prices.max() - irz_high) if direction == "up" else abs(irz_low - prices.min())
        max_move = max(max_move, distance)

    result["max_move_after_draw"] = round(max_move, 2)
    return result


def run_backtest(symbol_details: dict, timeframe: str, start_date: str, end_date: str):
    tf_lookback = get_dynamic_lookback(timeframe)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    results = []

    with open(OUTPUT_FILE, "w") as out:
        current = start
        while current <= end:
            if current.date() in us_holidays or current.weekday() >= 5:
                current += timedelta(days=1)
                continue

            for scan_t in SCAN_TIMES:
                scan_dt = datetime.combine(current.date(), scan_t)

                try:
                    df = fetch_ohlcv(symbol_details, timeframe, lookback_days=tf_lookback, current_time=scan_dt)

                    if not isinstance(df.index, pd.DatetimeIndex):
                        if "timestamp" in df.columns:
                            df["timestamp"] = pd.to_datetime(df["timestamp"])
                            df.set_index("timestamp", inplace=True)
                        else:
                            raise ValueError("No timestamp column and index is not datetime. Cannot proceed.")

                    report = run_analysis(symbol_details, timeframe)

                    fib_start = report.range_data.get("start_time")
                    if (
                        report.fib_data
                        and report.range_data
                        and report.irz_message
                        and fib_start
                        and fib_start <= scan_dt <= fib_start + timedelta(hours=24)
                    ):
                        outcome = monitor_irz_outcomes(
                            df,
                            report.range_data,
                            report.fib_data,
                            report.irz_message.get("direction")
                        )
                        outcome["symbol"] = symbol_details["db_symbol"]
                        outcome["timeframe"] = timeframe
                        outcome["scan_time"] = scan_dt.strftime("%Y-%m-%d %H:%M")
                        out.write(json.dumps(outcome) + "\n")
                        results.append(outcome)

                except Exception as e:
                    print(f"[Error] {scan_dt}: {e}")

            current += timedelta(days=1)

    summarize_backtest(results)


def summarize_backtest(results):
    print("\n📊 BACKTEST SUMMARY")
    total = len(results)
    if total == 0:
        print("No valid IRZ setups found.")
        return

    target_hits = Counter()
    for r in results:
        for t in r["targets_hit"]:
            target_hits[t] += 1

    print(f"Total setups analyzed: {total}")
    print("Target hit stats (within 24h of fib draw):")
    for level in ["0", "-0.236", "-0.618", "-1"]:
        count = target_hits.get(level, 0)
        pct = count / total
        print(f"  {level:<6}: {count} hits ({pct:.1%})")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", type=str)
    parser.add_argument("timeframe", type=str)
    parser.add_argument("--start", type=str, required=True)
    parser.add_argument("--end", type=str, required=True)
    args = parser.parse_args()

    resolved_symbol = resolve_symbol_alias(args.symbol)
    run_backtest(resolved_symbol, args.timeframe, args.start, args.end)
