# core/analyzer.py

from data.databento_client import fetch_ohlcv
from core.support_resistance import detect_support_resistance
from core.trendline_detector import detect_trendline
from core.range_detector import detect_body_range
from core.manipulation_detector import detect_manipulation
from core.irz_fib import calculate_irz_projection
from core.visualizer import plot_full_analysis


def run_analysis(symbol: str, timeframe: str = "1h") -> str:
    print(f"[Analyzer] Fetching data for {symbol} on {timeframe}")
    df = fetch_ohlcv(symbol, timeframe)

    if df is None or df.empty:
        return f"[ERROR] No data returned for {symbol} on {timeframe}"

    report = []

    report.append(f"📊 KawaiiTrader Report for {symbol} ({timeframe})")
    report.append("=" * 40)
    report.append(f"Fetched {len(df)} candles from Databento")

    # 🟦 Support / Resistance
    supports, resistances = detect_support_resistance(df)
    report.append(f"\n🟦 Support Levels: {supports}")
    report.append(f"🟥 Resistance Levels: {resistances}")

    # 🟩 Trendline Detection
    trendline_data = detect_trendline(df, timeframe, symbol)
    trendline_msgs = trendline_data["messages"]
    trendline_vectors = trendline_data["vectors"]
    report.extend(trendline_msgs)

    # 🟥 Range Detection
    range_info = detect_body_range(df, timeframe)
    report.append(f"\n🟥 {range_info['message']}")

    fib_data = None
    manipulation = {"status": "clean", "message": "", "direction": None}

    # 🟨 Manipulation Detection
    if range_info.get("is_range", False):
        manipulation = detect_manipulation(df, range_info)
        report.append(manipulation["message"])

        # 🟪 IRZ Fib Projection
        if manipulation["status"] == "manipulated":
            fib_data = calculate_irz_projection(
                range_low=range_info["range_low"],
                range_high=range_info["range_high"],
                manipulation_direction=manipulation["direction"]
            )
            report.append(fib_data["message"])
        else:
            report.append("🟪 No IRZ projected — waiting for return into range.")
    else:
        report.append("🟨 No valid range = manipulation detection skipped.")
        report.append("🟪 No manipulation = no IRZ projected.")

    # 🖼️ Generate Visual Chart
    chart_path = plot_full_analysis(
        df=df,
        symbol=symbol,
        timeframe=timeframe,
        support_levels=supports,
        resistance_levels=resistances,
        trendlines=trendline_vectors,
        fib_data=fib_data,
        range_data=range_info
    )

    report.append(f"\n📈 Chart saved to: `{chart_path}`")

    return "\n".join(report)
