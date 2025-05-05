from data.databento_client import fetch_ohlcv, get_dynamic_lookback
from core.support_resistance import detect_support_resistance
from core.trendline_detector import detect_trendline
from core.range_detector import detect_body_range
from core.manipulation_detector import detect_manipulation
from core.irz_fib import calculate_irz_projection
from core.visualizer import plot_full_analysis
from core.report_types import Report, Target, ManipulationEvent, Retracement

def run_analysis(symbol: str, timeframe: str = "1h") -> Report:
    

    target_candles = 365 if timeframe == "1d" else 120
    lookback_days = get_dynamic_lookback(timeframe, target_candles=target_candles)
    df = fetch_ohlcv(symbol, timeframe, lookback_days=lookback_days)

    if df is None or df.empty:
        raise ValueError(f"No data returned for {symbol} on {timeframe}")

    if len(df) < 10:
        print(f"⚠️ Only {len(df)} candles returned for {symbol} on {timeframe}")

    # 🟦 Support / Resistance
    supports, resistances = detect_support_resistance(df)

    # 📐 Trendlines
    trendline_data = detect_trendline(df, timeframe, symbol)
    trendline_vectors = trendline_data["vectors"]
    trendline_summary = "\n".join(trendline_data["messages"])

    # 🟥 Range Detection
    range_info = detect_body_range(df, timeframe)
    range_low = range_info.get("range_low")
    range_high = range_info.get("range_high")
    directional_bias = range_info.get("bias", "neutral")

    irz_zone = None
    irz_message = None
    targets = []
    manipulations = []
    retracements = []

    fib_data = None
    if range_info.get("is_range", False):
        manipulation = detect_manipulation(df, range_info)

        if manipulation["status"] == "manipulated":
            fib_data = calculate_irz_projection(
                range_low=range_low,
                range_high=range_high,
                manipulation_direction=manipulation["direction"]
            )

            irz_zone = fib_data.get("irz_zone")
            irz_message = fib_data.get("message")

            if fib_data:
                for t in fib_data.get("targets", []):
                    targets.append(t)
                for r in fib_data.get("retracements", []):
                    retracements.append(r)

        if manipulation["status"] != "clean":
            manipulations.append(ManipulationEvent(
                direction=manipulation["direction"],
                price=manipulation["price"],
                timestamp=manipulation["timestamp"]
            ))

    # ✅ Override bias based on IRZ projection
    if fib_data:
        direction = fib_data.get("projection_direction")
        if direction == "up":
            directional_bias = "bullish"
        elif direction == "down":
            directional_bias = "bearish"

    # 🖼️ Chart output
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

    return Report(
        symbol=symbol,
        timeframe=timeframe,
        range_low=range_low,
        range_high=range_high,
        directional_bias=directional_bias,
        irz_zone=irz_zone,
        irz_message=irz_message,
        trendline_summary=trendline_summary,
        support_levels=supports,
        resistance_levels=resistances,
        chart_path=chart_path,
        targets=targets,
        manipulations=manipulations,
        retracements=retracements
    )
