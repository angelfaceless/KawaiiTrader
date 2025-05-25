import numpy as np
import pandas as pd
from scipy.stats import linregress
import itertools
import math

# === Parameters ===
CANDIDATE_GENERATION_LOOKBACK = 20
MIN_PIVOTS_FOR_CANDIDATE = 3
MAX_PIVOTS_FOR_CANDIDATE = 5
MIN_R_SQUARED_FIT = 0.5

VALIDATION_LOOKBACK_CANDLES = 20
STRICT_TOUCH_TOLERANCE_POINTS = 0.5
GENERAL_TOUCH_TOLERANCE_POINTS = 1.5
BREACH_SIGNIFICANCE_POINTS = 3.0
MIN_STRICT_TOUCHES_REQUIRED = 2
MIN_RESPECT_RATIO = 0.80

# === Scoring Weights ===
W_STRICT_TOUCHES = 50
W_RESPECT_RATIO = 30
W_RECENCY_STRICT_TOUCH = 20
W_R_SQUARED_PIVOTS = 5
W_GENERAL_TOUCHES = 2
W_BODY_PENETRATION_PENALTY = -20
W_BREACH_PENALTY = -100
W_SLOPE_ANGLE = 5
MIN_ACCEPTABLE_SCORE = 20
OPTIMAL_SLOPE_DEGREES_MIN = 10
OPTIMAL_SLOPE_DEGREES_MAX = 60

VOLATILE_SYMBOLS = {"NQ", "BTC", "ETH", "RTY", "MGC", "GC", "CL", "NG"}

def is_volatile(symbol: str) -> bool:
    return symbol.upper().split(".")[0] in VOLATILE_SYMBOLS

def adjust_trendline_parameters(symbol: str, timeframe: str):
    is_high_tf = timeframe in ["1h", "1d", "1w", "1mo"]
    volatile = is_volatile(symbol)
    params = {
        "STRICT_TOUCH_TOLERANCE_POINTS": 0.5,
        "GENERAL_TOUCH_TOLERANCE_POINTS": 1.5,
        "BREACH_SIGNIFICANCE_POINTS": 3.0,
        "MIN_STRICT_TOUCHES_REQUIRED": 2,
        "MIN_RESPECT_RATIO": 0.80,
        "MAX_PIVOTS_FOR_CANDIDATE": 5,
    }
    if volatile and is_high_tf:
        params.update({
            "STRICT_TOUCH_TOLERANCE_POINTS": 1.0,
            "GENERAL_TOUCH_TOLERANCE_POINTS": 2.5,
            "BREACH_SIGNIFICANCE_POINTS": 5.0,
            "MIN_STRICT_TOUCHES_REQUIRED": 1,
            "MIN_RESPECT_RATIO": 0.60,
            "MAX_PIVOTS_FOR_CANDIDATE": 6,
        })
    return params

def detect_pivots(df, window=5):
    highs, lows = df["high"], df["low"]
    pivot_highs, pivot_lows = [], []
    for i in range(window, len(df) - window):
        if highs.iloc[i] == max(highs.iloc[i - window:i + window + 1]):
            pivot_highs.append((i, highs.iloc[i]))
        if lows.iloc[i] == min(lows.iloc[i - window:i + window + 1]):
            pivot_lows.append((i, lows.iloc[i]))
    return pivot_highs, pivot_lows

def _fit_regression_to_points(points, r_threshold):
    if len(points) < 2: return None
    x = np.array([pt[0] for pt in points])
    y = np.array([pt[1] for pt in points])
    if len(np.unique(x)) < 2: return None
    try:
        slope, intercept, r_value, *_ = linregress(x, y)
    except ValueError:
        return None
    if r_value**2 < r_threshold:
        return None
    return {
        "slope": slope, "intercept": intercept,
        "r_squared": r_value**2, "start_index": x[0],
        "points": points,
    }

def generate_candidate_pivot_combinations(pivots, lookback, min_pts, max_pts):
    if not pivots or len(pivots) < min_pts: return []
    pivots = pivots[-lookback:] if len(pivots) >= min_pts else pivots
    out = []
    for i in range(min_pts, min(len(pivots), max_pts)+1):
        out.extend(list(itertools.combinations(pivots, i)))
    return [list(c) for c in out]

def _validate_candidate_trendline_refined(df, trend, kind, validation_lookback,
                                          strict_touch_tolerance,
                                          general_touch_tolerance,
                                          breach_significance):
    slope, intercept = trend["slope"], trend["intercept"]
    recent = df.iloc[-validation_lookback:] if len(df) >= validation_lookback else df

    n_strict, n_general, n_body, n_breach, respect_count = 0, 0, 0, 0, 0
    recency = validation_lookback

    for i, candle in enumerate(recent.itertuples()):
        idx = df.index.get_loc(candle.Index)
        trend_val = slope * idx + intercept
        is_strict = False

        if kind == "support":
            if abs(candle.low - trend_val) <= strict_touch_tolerance and (
                candle.close > trend_val - strict_touch_tolerance or
                abs(candle.close - trend_val) <= strict_touch_tolerance
            ):
                is_strict = True
        else:
            if abs(candle.high - trend_val) <= strict_touch_tolerance and (
                candle.close < trend_val + strict_touch_tolerance or
                abs(candle.close - trend_val) <= strict_touch_tolerance
            ):
                is_strict = True

        if is_strict:
            n_strict += 1
            recency = len(recent) - 1 - i

        if candle.low - general_touch_tolerance <= trend_val <= candle.high + general_touch_tolerance:
            n_general += 1

        if min(candle.open, candle.close) < trend_val < max(candle.open, candle.close):
            n_body += 1

        if kind == "support" and candle.close < trend_val - breach_significance:
            n_breach += 1
        if kind == "resistance" and candle.close > trend_val + breach_significance:
            n_breach += 1

        if kind == "support" and candle.low >= trend_val - general_touch_tolerance and candle.close >= trend_val - general_touch_tolerance:
            respect_count += 1
        if kind == "resistance" and candle.high <= trend_val + general_touch_tolerance and candle.close <= trend_val + general_touch_tolerance:
            respect_count += 1

    respect_ratio = respect_count / len(recent) if len(recent) > 0 else 0
    trend["validation_stats"] = {
        "num_strict_touches": n_strict,
        "num_general_touches": n_general,
        "num_body_penetrations": n_body,
        "num_breaches": n_breach,
        "last_strict_touch_recency": recency,
        "respect_ratio": respect_ratio
    }
    return trend

def _score_candidate_trendline_refined(cand, validation_lookback):
    stats = cand["validation_stats"]
    slope_deg = math.degrees(math.atan(cand["slope"]))

    total_score = (
        stats["num_strict_touches"] * W_STRICT_TOUCHES +
        stats["respect_ratio"] * W_RESPECT_RATIO +
        (validation_lookback - stats["last_strict_touch_recency"]) * W_RECENCY_STRICT_TOUCH +
        cand["r_squared"] * W_R_SQUARED_PIVOTS +
        stats["num_general_touches"] * W_GENERAL_TOUCHES +
        stats["num_body_penetrations"] * W_BODY_PENETRATION_PENALTY +
        stats["num_breaches"] * W_BREACH_PENALTY +
        (W_SLOPE_ANGLE if OPTIMAL_SLOPE_DEGREES_MIN <= abs(slope_deg) <= OPTIMAL_SLOPE_DEGREES_MAX
         else -W_SLOPE_ANGLE if abs(slope_deg) < OPTIMAL_SLOPE_DEGREES_MIN / 2 or abs(slope_deg) > OPTIMAL_SLOPE_DEGREES_MAX * 1.5 else 0)
    )

    cand["score_details"] = {"total_score": total_score}
    cand["total_score"] = total_score
    return cand

def fit_trendline_iterative(df, pivots, kind):
    if len(pivots) < MIN_PIVOTS_FOR_CANDIDATE:
        return None

    candidates = generate_candidate_pivot_combinations(pivots, CANDIDATE_GENERATION_LOOKBACK, MIN_PIVOTS_FOR_CANDIDATE, MAX_PIVOTS_FOR_CANDIDATE)

    scored = []
    for combo in candidates:
        fit = _fit_regression_to_points(combo, MIN_R_SQUARED_FIT)
        if not fit:
            continue
        fit["source"] = kind
        validated = _validate_candidate_trendline_refined(df, fit, kind,
            VALIDATION_LOOKBACK_CANDLES, STRICT_TOUCH_TOLERANCE_POINTS,
            GENERAL_TOUCH_TOLERANCE_POINTS, BREACH_SIGNIFICANCE_POINTS)
        stats = validated["validation_stats"]
        if stats["num_strict_touches"] < MIN_STRICT_TOUCHES_REQUIRED:
            continue
        if stats["respect_ratio"] < MIN_RESPECT_RATIO:
            continue
        if stats["num_breaches"] > 1:
            continue
        scored.append(_score_candidate_trendline_refined(validated, VALIDATION_LOOKBACK_CANDLES))

    if not scored:
        return None

    best = max(scored, key=lambda c: c["total_score"])
    return best if best["total_score"] >= MIN_ACCEPTABLE_SCORE else None

def classify_trendline(df, trend, timeframe="1h"):
    slope, intercept = trend["slope"], trend["intercept"]
    tf_map = {"1min": 1440, "5min": 288, "15min": 96, "30min": 48, "1h": 24, "2h": 12, "3h": 8, "4h": 6, "6h": 4, "12h": 2, "1d": 1}
    lookback = min(3 * tf_map.get(timeframe, 24), len(df))
    recent = df.tail(lookback)
    x = np.arange(len(df) - lookback, len(df))
    trend_vals = slope * x + intercept
    closes = recent["close"].values
    above, below = np.mean(closes > trend_vals), np.mean(closes < trend_vals)
    if above > 0.7: return "Support"
    if below > 0.7: return "Resistance"
    if trend["source"] == "resistance" and above > 0.4 and slope > 0: return "Support (flipped from resistance)"
    if trend["source"] == "support" and below > 0.4 and slope < 0: return "Resistance (flipped from support)"
    return "Ambiguous"

def detect_trendline(df: pd.DataFrame, timeframe: str = "1h", symbol: str = "ES"):
    def run_detection(strict_touches):
        global STRICT_TOUCH_TOLERANCE_POINTS, GENERAL_TOUCH_TOLERANCE_POINTS
        global BREACH_SIGNIFICANCE_POINTS, MIN_STRICT_TOUCHES_REQUIRED
        global MIN_RESPECT_RATIO, MAX_PIVOTS_FOR_CANDIDATE
        params = adjust_trendline_parameters(symbol, timeframe)
        STRICT_TOUCH_TOLERANCE_POINTS = params["STRICT_TOUCH_TOLERANCE_POINTS"]
        GENERAL_TOUCH_TOLERANCE_POINTS = params["GENERAL_TOUCH_TOLERANCE_POINTS"]
        BREACH_SIGNIFICANCE_POINTS = params["BREACH_SIGNIFICANCE_POINTS"]
        MIN_STRICT_TOUCHES_REQUIRED = strict_touches
        MIN_RESPECT_RATIO = params["MIN_RESPECT_RATIO"]
        MAX_PIVOTS_FOR_CANDIDATE = params["MAX_PIVOTS_FOR_CANDIDATE"]
        ph, pl = detect_pivots(df)
        return fit_trendline_iterative(df, pl, "support"), fit_trendline_iterative(df, ph, "resistance")

    support, resistance = run_detection(1)
    if not support and not resistance:
        support, resistance = run_detection(0)

    messages, vectors = {}, {}
    current_price = df["close"].iloc[-1]
    current_low = df["low"].iloc[-1]
    current_high = df["high"].iloc[-1]
    current_idx = len(df) - 1

    def enrich(trend, role):
        slope, intercept = trend["slope"], trend["intercept"]
        trend_val = slope * current_idx + intercept
        dist = round(abs(current_price - trend_val), 2)
        icon = "✋" if current_low <= trend_val <= current_high else "🟰" if abs(current_price - trend_val) <= 5 else "🔺" if trend_val > current_price else "🔻"
        position = "touching" if icon == "✋" else f"at {current_price:.2f}" if icon == "🟰" else "above" if icon == "🔺" else "below"
        trend.update({
            "trendline_value": round(trend_val, 2),
            "distance": dist,
            "position_text": position,
            "icon": icon,
            "timeframe": timeframe,
            "role": role,
            "touch_points": [f"{p[1]:.2f}" for p in trend["points"]]
        })
        return trend

    for trend, label in [(support, "Support"), (resistance, "Resistance")]:
        if trend:
            role = classify_trendline(df, trend, timeframe)
            enriched = enrich(trend, role)
            vectors[label] = enriched
            color = "🟩" if "Support" in role else "🟥"
            messages[label] = (
                f"{color} {role} trendline detected ({timeframe})\n"
                f"  • Position: {enriched['icon']} {enriched['position_text']}\n"
                f"  • Distance: {enriched['distance']} pts\n"
                f"  • Touch points: {', '.join(enriched['touch_points'])}"
            )

    if not messages:
        return {"messages": [f"No active trendline near current price ({timeframe})"], "vectors": vectors}
    return {"messages": list(messages.values()), "vectors": vectors}
