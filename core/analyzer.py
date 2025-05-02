from dotenv import load_dotenv
load_dotenv()

import os
print("[DEBUG] DATABENTO_API_KEY:", os.environ.get("DATABENTO_API_KEY"))

from data.databento_client import fetch_ohlcv
from core.support_resistance import detect_support_resistance
from core.trendline_detector import detect_trendline
from core.range_detector import detect_body_range
from core.manipulation_detector import detect_manipulation
from core.irz_fib import calculate_irz_projection
from utils.symbols import resolve_symbol_alias


def run_analysis(symbol: str, timeframe: str = "1h") -> str:
    try:
        from tabulate import tabulate
        import pandas as pd

        resolved_symbol = resolve_symbol_alias(symbol)
        print(f"[Analyzer] Fetching data for {resolved_symbol} on {timeframe}")
        df = fetch_ohlcv(resolved_symbol, timeframe)

        report = []
        report.append(f"📊 KawaiiTrader Report for {resolved_symbol} ({timeframe})")
        report.append("=" * 40)
        report.append(f"Fetched {len(df)} candles from Databento")

        # 🟦 Support / Resistance
        supports, resistances = detect_support_resistance(df)
        supports = [float(x) for x in supports]
        resistances = [float(x) for x in resistances]
        report.append(f"\n🟦 Support Levels: {supports}")
        report.append(f"🟥 Resistance Levels: {resistances}")

        # 🟩 Trendline Detection
        trendline_msgs = detect_trendline(df, timeframe)
        report.extend(trendline_msgs)

        # 🟥 Range Detection
        range_info = detect_body_range(df, timeframe)
        report.append(f"\n🟥 {range_info['message']}")

        # 🟨 Manipulation Detection
        if range_info.get("is_range", False):
            manipulation_result = detect_manipulation(df, timeframe)
            report.append(manipulation_result["message"])

            manipulations = manipulation_result.get("manipulations", [])
            breakouts = manipulation_result.get("breakouts", [])
            bias = manipulation_result.get("bias", "neutral")

            # 🧼 Filter out malformed dicts before DataFrame creation
            df_m = pd.DataFrame([m for m in manipulations if all(k in m for k in ("timestamp", "price", "direction"))])
            df_b = pd.DataFrame([b for b in breakouts if all(k in b for k in ("timestamp", "price", "direction"))])

            if not df_m.empty:
                df_m["timestamp"] = pd.to_datetime(df_m["timestamp"]).dt.tz_convert("US/Eastern")
                report.append(f"\n### 🕵️‍♂️ Manipulation Events ({len(df_m)} total)")
                report.append(tabulate(df_m, headers="keys", tablefmt="github", showindex=False))

            if not df_b.empty:
                df_b["timestamp"] = pd.to_datetime(df_b["timestamp"]).dt.tz_convert("US/Eastern")
                report.append(f"\n### 🚀 Breakout Events ({len(df_b)} total)")
                report.append(tabulate(df_b, headers="keys", tablefmt="github", showindex=False))

            if bias == "bullish":
                report.append("\n📈 **Overall Bias: Bullish**")
            elif bias == "bearish":
                report.append("\n📉 **Overall Bias: Bearish**")
            else:
                report.append("\n⚖️ **Overall Bias: Neutral**")

            # 🟪 IRZ Fib Projection
            if manipulation_result["status"] == "manipulated":
                manipulation_direction = (
                    manipulations[-1]["direction"] if manipulations else (
                        breakouts[-1]["direction"] if breakouts else None
                    )
                )

                if manipulation_direction not in ("above", "below"):
                    print(f"[WARN] Invalid manipulation direction: {manipulation_direction}")
                    manipulation_direction = "above"

                fib = calculate_irz_projection(
                    range_low=range_info["range_low"],
                    range_high=range_info["range_high"],
                    manipulation_direction=manipulation_direction,
                    breakouts=df_b.to_dict("records")
                )

                levels = fib["levels"]
                irz = fib["irz"]
                targets = fib["targets"]
                direction = fib["direction"]

                report.append(f"\n### 📐 IRZ Fibonacci Projection ({direction.capitalize()})")

                for level in sorted(levels, key=lambda x: -x if direction == "down" else x):
                    label = "IRZ" if level in irz else "Target" if level in targets else "Other"
                    price = levels[level]
                    report.append(f"- **{level}** ({label}): {price:.2f}")

        return "\n".join(report)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"[ERROR] Report failed for {symbol} on {timeframe}: {e}"
