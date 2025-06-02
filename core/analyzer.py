from data.databento_client import fetch_ohlcv, get_dynamic_lookback
from core.support_resistance import detect_support_resistance
from core.trendline_detector import detect_trendline
from core.range_detector import detect_body_range
from core.manipulation_detector import detect_manipulation
from core.irz_fib import calculate_irz_projection
from core.visualizer import plot_full_analysis
from core.report_types import Report, Target, ManipulationEvent, Retracement
from utils.htfcontext_helper import compare_levels_with_htf


def truncate_touch_points(message: str, max_points: int = 10) -> str:
    if "Touch points:" not in message:
        return message
    prefix, points_part = message.split("Touch points:", 1)
    points = [p.strip() for p in points_part.split(",") if p.strip()]
    if len(points) <= max_points:
        return f"{prefix}Touch points: {', '.join(points)}"
    truncated = points[:max_points]
    return f"{prefix}Touch points: {', '.join(truncated)}... (+{len(points) - max_points} more)"


def check_kawaii_sell_criteria(range_high, manipulation, confidence, manipulations) -> tuple[bool, list]:
    qualifying_resistances = []
    resistance_conf = confidence.get("resistance", {})

    for lvl_str, meta in resistance_conf.items():
        if not isinstance(meta, dict):
            continue
        if meta.get("level") in {"strong", "medium"} and meta.get("matched_timeframes"):
            try:
                lvl = float(lvl_str)
                if abs(lvl - range_high) <= 5:
                    qualifying_resistances.append(lvl)
            except ValueError:
                continue

    if not qualifying_resistances:
        return False, []

    for m in manipulations:
        if m.direction == "up":
            return True, qualifying_resistances

    return False, []


def run_analysis(symbol_details: dict, timeframe: str = "1h", htf_cache: dict = None) -> Report:
    input_symbol = symbol_details.get("input_symbol", symbol_details.get("db_symbol", "Unknown"))
    target_candles = 365 if timeframe == "1d" else 120
    lookback_days = get_dynamic_lookback(timeframe, target_candles=target_candles)

    if htf_cache is not None and timeframe in {"4h", "1d"}:
        symbol_cache = htf_cache.get(input_symbol, {})
        if timeframe in symbol_cache:
            df = symbol_cache[timeframe]
        else:
            df = fetch_ohlcv(symbol_details, timeframe, lookback_days=lookback_days)
            if input_symbol not in htf_cache:
                htf_cache[input_symbol] = {}
            htf_cache[input_symbol][timeframe] = df
    else:
        df = fetch_ohlcv(symbol_details, timeframe, lookback_days=lookback_days)

    if df is None or df.empty:
        raise ValueError(f"No data returned for {input_symbol} on {timeframe}")
    if len(df) < 10:
        print(f"⚠️ Only {len(df)} candles returned for {input_symbol} on {timeframe}")

    current_price = float(df["close"].iloc[-1])
    current_price_time = df.index[-1].isoformat()

    supports, resistances = detect_support_resistance(df)

    trendline_data = detect_trendline(df, timeframe, input_symbol)
    raw_vectors = trendline_data["vectors"]
    trendline_vectors = {}
    annotated_messages = []

    visible_min = df["low"].min()
    visible_max = df["high"].max()

    for role, trend in raw_vectors.items():
        clean_key = role.lower().split()[0]
        slope = trend["slope"]
        intercept = trend["intercept"]
        start_idx = trend["start_index"]
        x_vals = list(range(start_idx, len(df)))
        y_vals = [slope * x + intercept for x in x_vals]
        trendline_vectors[clean_key] = {"slope": slope, "intercept": intercept, "start_index": start_idx}

    for msg in trendline_data["messages"]:
        truncated_msg = truncate_touch_points(msg)
        if "Touch points:" in truncated_msg:
            if max(y_vals) < visible_min:
                truncated_msg += " _(below visible range)_"
            elif min(y_vals) > visible_max:
                truncated_msg += " _(above visible range)_"
        annotated_messages.append(truncated_msg)

    trendline_summary = "\n".join(annotated_messages)

    confidence = compare_levels_with_htf(
        symbol_details,
        timeframe,
        df,
        supports,
        resistances,
        trendline_vectors
    )

    range_info = detect_body_range(df, timeframe)
    print(f"🟪 Range Info → {range_info['message']}")
    range_low = range_info.get("range_low")
    range_high = range_info.get("range_high")
    directional_bias = range_info.get("bias", "neutral")

    support_aligned = any(abs(s - range_low) / s < 0.002 for s in supports if range_low is not None)
    range_info["support_aligned"] = support_aligned
    if support_aligned:
        range_info["message"] += " | 🟢 Range low aligns with support"
    else:
        range_info["message"] += " | ⚪ No support confluence at range low"

    irz_zone = None
    irz_message = None
    targets = []
    manipulations = []
    retracements = []
    fib_data = None
    manipulation = {}

    if range_info.get("is_range", False):
        manipulation = detect_manipulation(df, range_info)
        print(f"🟨 Manipulation Status → {manipulation['status']} | {manipulation['message']}")

        if manipulation["status"] == "manipulated":
            fib_data = calculate_irz_projection(
                range_low=range_low,
                range_high=range_high,
                manipulation_direction=manipulation["direction"]
            )
            irz_zone = fib_data.get("irz_zone")
            irz_message = fib_data.get("message")
            targets.extend(fib_data.get("targets", []))
            retracements.extend(fib_data.get("retracements", []))

        if manipulation["status"] != "clean":
            manipulations.append(ManipulationEvent(
                direction=manipulation["direction"],
                price=manipulation["price"],
                timestamp=manipulation["timestamp"]
            ))

    if fib_data:
        direction = fib_data.get("projection_direction")
        if direction == "up":
            directional_bias = "bullish"
        elif direction == "down":
            directional_bias = "bearish"

    kawaii_buy = (
        range_info.get("is_range", False) and
        range_info.get("support_aligned", False) and
        confidence.get("support", {}).get("aligned_with_htf", {}).get("count", 0) > 0 and
        manipulation.get("direction") == "down"
    )

    kawaii_sell, kawaii_sell_resistances = check_kawaii_sell_criteria(
        range_high=range_high,
        manipulation=manipulation,
        confidence=confidence,
        manipulations=manipulations
    )

    # ✅ Pass HTF confidence info to chart
    chart_path = plot_full_analysis(
        df=df,
        symbol=input_symbol,
        timeframe=timeframe,
        support_levels=supports,
        resistance_levels=resistances,
        trendlines=trendline_vectors,
        fib_data=fib_data,
        range_data={**range_info, "htf_confidence": confidence},  # ✅ Surgical fix
        kawaii_sell=kawaii_sell,
        kawaii_sell_resistances=kawaii_sell_resistances
    )

    return Report(
        symbol=input_symbol,
        timeframe=timeframe,
        range_low=range_low,
        range_high=range_high,
        directional_bias=directional_bias,
        irz_zone=irz_zone,
        irz_message=irz_message,
        trendline_summary=trendline_summary,
        trendlines=trendline_vectors,
        support_levels=supports,
        resistance_levels=resistances,
        chart_path=chart_path,
        targets=targets,
        manipulations=manipulations,
        retracements=retracements,
        current_price=current_price,
        current_price_time=current_price_time,
        confidence=confidence,
        kawaii_buy=kawaii_buy,
        kawaii_sell=kawaii_sell,
        kawaii_sell_resistances=kawaii_sell_resistances
    )
