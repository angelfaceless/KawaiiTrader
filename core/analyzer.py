# kawaiitrader/core/analyzer.py

from data.databento_client import fetch_ohlcv
from core.support_resistance import detect_support_resistance
from core.trendline_detector import detect_trendline
from core.range_detector import detect_body_range
from core.manipulation_detector import detect_manipulation
from core.irz_fib import calculate_irz_projection

def run_analysis(symbol: str, timeframe: str = "1h") -> str:
    print(f"[Analyzer] Fetching data for {symbol} on {timeframe}")
    df = fetch_ohlcv(symbol, timeframe)

    report = []

    report.append(f"📊 KawaiiTrader Report for {symbol} ({timeframe})")
    report.append("=" * 40)
    report.append(f"Fetched {len(df)} candles from Databento")

    # 🟦 Support / Resistance
    supports, resistances = detect_support_resistance(df)
    report.append(f"\n🟦 Support Levels: {supports}")
    report.append(f"🟥 Resistance Levels: {resistances}")

    # 🟩 Trendline Detection
    trendline_msgs = detect_trendline(df, timeframe)
    report.extend(trendline_msgs)

    # 🟥 Range Detection (Body-based)
    range_info = detect_body_range(df, timeframe)
    report.append(f"\n🟥 {range_info['message']}")

    # 🟨 Manipulation Detection
    manipulation = detect_manipulation(df, range_info["range_low"], range_info["range_high"])
    report.append(manipulation["message"])

    # 🟪 IRZ Fib Projection
    if manipulation["manipulated"]:
        fib = calculate_irz_projection(
            range_low=range_info["range_low"],
            range_high=range_info["range_high"],
            manipulation_direction=manipulation["direction"]
        )
        report.append(fib["message"])
    else:
        report.append("🟪 No manipulation = no IRZ projected.")

    return "\n".join(report)
