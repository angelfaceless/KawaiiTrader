import numpy as np
import pandas as pd
from scipy.stats import linregress
import itertools
import math

# Parameters for iterative fitting
CANDIDATE_GENERATION_LOOKBACK = 20 # Reduced for performance
MIN_PIVOTS_FOR_CANDIDATE = 3
MAX_PIVOTS_FOR_CANDIDATE = 5 # Reduced for performance
MIN_R_SQUARED_FIT = 0.5 

# Parameters for validation (more aligned with visual significance)
VALIDATION_LOOKBACK_CANDLES = 20 
STRICT_TOUCH_TOLERANCE_POINTS = 0.5 
GENERAL_TOUCH_TOLERANCE_POINTS = 1.5 
BREACH_SIGNIFICANCE_POINTS = 3.0 
MIN_STRICT_TOUCHES_REQUIRED = 2 
MIN_RESPECT_RATIO = 0.80 

# Scoring Weights (tuned to prioritize visual significance)
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

def detect_pivots(df, window=5):
    highs = df["high"]
    lows = df["low"]
    pivot_highs = []
    pivot_lows = []
    for i in range(window, len(df) - window):
        if highs.iloc[i] == max(highs.iloc[i - window:i + window + 1]):
            pivot_highs.append((i, highs.iloc[i]))
        if lows.iloc[i] == min(lows.iloc[i - window:i + window + 1]):
            pivot_lows.append((i, lows.iloc[i]))
    return pivot_highs, pivot_lows

def _fit_regression_to_points(points, r_threshold):
    if len(points) < 2:
        return None
    x_raw = np.array([pt[0] for pt in points])
    y = np.array([pt[1] for pt in points])
    if len(np.unique(x_raw)) < 2:
        return None
    try:
        slope, intercept_orig, r_value, _, _ = linregress(x_raw, y)
    except ValueError:
        return None
    if r_value**2 < r_threshold:
        return None
    return {
        "slope": slope,
        "intercept": intercept_orig,
        "r_squared": r_value**2,
        "start_index": x_raw[0],
        "points": points,
    }

def generate_candidate_pivot_combinations(all_pivots, lookback_count, min_pivots, max_pivots):
    if not all_pivots or len(all_pivots) < min_pivots:
        return []
    recent_pivots = all_pivots[-lookback_count:]
    if len(recent_pivots) < min_pivots:
        if len(all_pivots) >= min_pivots:
            recent_pivots = all_pivots
        else:
            return []
    candidate_combinations = []
    for i in range(min_pivots, min(len(recent_pivots), max_pivots) + 1):
        for combo in itertools.combinations(recent_pivots, i):
            candidate_combinations.append(list(combo))
    return candidate_combinations

def _validate_candidate_trendline_refined(df, candidate_trend, kind="support",
                                 validation_lookback=VALIDATION_LOOKBACK_CANDLES,
                                 strict_touch_tolerance=STRICT_TOUCH_TOLERANCE_POINTS,
                                 general_touch_tolerance=GENERAL_TOUCH_TOLERANCE_POINTS,
                                 breach_significance=BREACH_SIGNIFICANCE_POINTS):
    slope = candidate_trend["slope"]
    intercept = candidate_trend["intercept"]
    if len(df) < validation_lookback:
        recent_candles_df = df
    else:
        recent_candles_df = df.iloc[-validation_lookback:]

    num_strict_touches = 0
    num_general_touches = 0
    num_body_penetrations = 0
    num_breaches = 0
    last_strict_touch_recency = validation_lookback 
    respecting_candles_count = 0

    for i in range(len(recent_candles_df)):
        candle = recent_candles_df.iloc[i]
        candle_idx = df.index.get_loc(candle.name)
        trend_value_at_candle = slope * candle_idx + intercept
        
        is_strict_touch = False
        if kind == "support":
            if (abs(candle["low"] - trend_value_at_candle) <= strict_touch_tolerance and candle["close"] > trend_value_at_candle - strict_touch_tolerance) or \
               (abs(candle["low"] - trend_value_at_candle) <= strict_touch_tolerance and abs(candle["close"] - trend_value_at_candle) <= strict_touch_tolerance): 
                is_strict_touch = True
        elif kind == "resistance":
            if (abs(candle["high"] - trend_value_at_candle) <= strict_touch_tolerance and candle["close"] < trend_value_at_candle + strict_touch_tolerance) or \
               (abs(candle["high"] - trend_value_at_candle) <= strict_touch_tolerance and abs(candle["close"] - trend_value_at_candle) <= strict_touch_tolerance): 
                is_strict_touch = True
        if is_strict_touch:
            num_strict_touches += 1
            last_strict_touch_recency = (len(recent_candles_df) - 1) - i

        if candle["low"] - general_touch_tolerance <= trend_value_at_candle <= candle["high"] + general_touch_tolerance:
            num_general_touches += 1

        if min(candle["open"], candle["close"]) < trend_value_at_candle < max(candle["open"], candle["close"]):
            num_body_penetrations += 1

        if kind == "support":
            if candle["close"] < trend_value_at_candle - breach_significance:
                num_breaches += 1
        elif kind == "resistance":
            if candle["close"] > trend_value_at_candle + breach_significance:
                num_breaches += 1
        
        if kind == "support":
            if candle["low"] >= trend_value_at_candle - general_touch_tolerance and candle["close"] >= trend_value_at_candle - general_touch_tolerance:
                respecting_candles_count +=1
        elif kind == "resistance":
            if candle["high"] <= trend_value_at_candle + general_touch_tolerance and candle["close"] <= trend_value_at_candle + general_touch_tolerance:
                respecting_candles_count +=1
            
    respect_ratio = respecting_candles_count / len(recent_candles_df) if len(recent_candles_df) > 0 else 0

    candidate_trend["validation_stats"] = {
        "num_strict_touches": num_strict_touches,
        "num_general_touches": num_general_touches,
        "num_body_penetrations": num_body_penetrations,
        "num_breaches": num_breaches,
        "last_strict_touch_recency": last_strict_touch_recency,
        "respect_ratio": respect_ratio,
        "validation_lookback_used": len(recent_candles_df)
    }
    return candidate_trend

def _score_candidate_trendline_refined(candidate, validation_lookback=VALIDATION_LOOKBACK_CANDLES):
    stats = candidate["validation_stats"]
    r_squared_pivots = candidate["r_squared"]
    slope_rad = math.atan(candidate["slope"])
    slope_deg = math.degrees(slope_rad)

    score_strict_touches = stats["num_strict_touches"] * W_STRICT_TOUCHES
    score_respect_ratio = stats["respect_ratio"] * W_RESPECT_RATIO 
    recency_value_strict = validation_lookback - stats["last_strict_touch_recency"]
    score_recency_strict = recency_value_strict * W_RECENCY_STRICT_TOUCH
    score_r_squared_pivots = r_squared_pivots * W_R_SQUARED_PIVOTS
    score_general_touches = stats["num_general_touches"] * W_GENERAL_TOUCHES
    penalty_body_penetration = stats["num_body_penetrations"] * W_BODY_PENETRATION_PENALTY
    penalty_breach = stats["num_breaches"] * W_BREACH_PENALTY
    
    slope_angle_score = 0
    if OPTIMAL_SLOPE_DEGREES_MIN <= abs(slope_deg) <= OPTIMAL_SLOPE_DEGREES_MAX:
        slope_angle_score = W_SLOPE_ANGLE
    elif abs(slope_deg) < OPTIMAL_SLOPE_DEGREES_MIN / 2 or abs(slope_deg) > OPTIMAL_SLOPE_DEGREES_MAX * 1.5: 
        slope_angle_score = -W_SLOPE_ANGLE
        
    total_score = (score_strict_touches + score_respect_ratio + score_recency_strict +
                   score_r_squared_pivots + score_general_touches + 
                   penalty_body_penetration + penalty_breach + slope_angle_score)
    
    candidate["score_details"] = {
        "total_score": total_score,
        "score_strict_touches": score_strict_touches,
        "score_respect_ratio": score_respect_ratio,
        "score_recency_strict": score_recency_strict,
        "score_r_squared_pivots": score_r_squared_pivots,
        "score_general_touches": score_general_touches,
        "penalty_body_penetration": penalty_body_penetration,
        "penalty_breach": penalty_breach,
        "slope_angle_score": slope_angle_score,
        "slope_degrees": slope_deg
    }
    candidate["total_score"] = total_score
    return candidate

def fit_trendline_iterative(df_full, all_pivots, kind="support", r_threshold=MIN_R_SQUARED_FIT,
                              lookback_count=CANDIDATE_GENERATION_LOOKBACK,
                              min_pivots=MIN_PIVOTS_FOR_CANDIDATE,
                              max_pivots=MAX_PIVOTS_FOR_CANDIDATE):
    if len(all_pivots) < min_pivots:
        return None

    candidate_pivot_sets = generate_candidate_pivot_combinations(all_pivots, lookback_count, min_pivots, max_pivots)
    if not candidate_pivot_sets:
        return None

    scored_candidates = []
    for pivot_set in candidate_pivot_sets:
        fit_result = _fit_regression_to_points(pivot_set, r_threshold)
        if fit_result:
            fit_result["source"] = kind
            validated_candidate = _validate_candidate_trendline_refined(df_full, fit_result, kind)
            stats = validated_candidate["validation_stats"]
            if stats["num_strict_touches"] < MIN_STRICT_TOUCHES_REQUIRED :
                continue
            if stats["respect_ratio"] < MIN_RESPECT_RATIO:
                continue
            if stats["num_breaches"] > 1 :
                continue

            scored_candidate = _score_candidate_trendline_refined(validated_candidate)
            scored_candidates.append(scored_candidate)

    if not scored_candidates:
        return None

    best_candidate = max(scored_candidates, key=lambda c: c["total_score"])
    
    if best_candidate["total_score"] < MIN_ACCEPTABLE_SCORE:
        return None
        
    return best_candidate

def classify_trendline(df, trend_meta, timeframe="1h"):
    slope = trend_meta["slope"]
    intercept = trend_meta["intercept"]
    tf_map = {
        "1min": 1440, "5min": 288, "15min": 96, "30min": 48,
        "1h": 24, "2h": 12, "3h": 8, "4h": 6, "6h": 4,
        "12h": 2, "1d": 1,
    }
    candles_per_day = tf_map.get(timeframe.lower(), 24)
    lookback = min(3 * candles_per_day, len(df))
    recent_df = df.tail(lookback)
    x_vals_for_classification = np.arange(len(df) - lookback, len(df))
    trend_values_for_classification = slope * x_vals_for_classification + intercept
    closes = recent_df["close"].values
    above_ratio = np.mean(closes > trend_values_for_classification)
    below_ratio = np.mean(closes < trend_values_for_classification)
    if above_ratio > 0.7: return "Support"
    if below_ratio > 0.7: return "Resistance"
    if trend_meta["source"] == "resistance" and above_ratio > 0.4 and slope > 0: return "Support (flipped from resistance)"
    if trend_meta["source"] == "support" and below_ratio > 0.4 and slope < 0: return "Resistance (flipped from support)"
    return "Ambiguous"

def detect_trendline(df: pd.DataFrame, timeframe: str = "1h", symbol: str = "ES"):
    pivot_highs, pivot_lows = detect_pivots(df)
    support_trend = fit_trendline_iterative(df, pivot_lows, "support")
    resistance_trend = fit_trendline_iterative(df, pivot_highs, "resistance")

    messages = []
    vectors = {}
    current_idx = len(df) - 1
    current_price = df["close"].iloc[-1]
    current_low = df["low"].iloc[-1]
    current_high = df["high"].iloc[-1]

    def enrich_trend(trend, role, current_price_val):
        slope = trend["slope"]
        intercept = trend["intercept"]
        trend_value = slope * current_idx + intercept
        distance = round(abs(current_price_val - trend_value), 2)
        
        score_details = trend.get("score_details", {})
        total_score = score_details.get("total_score", "N/A")
        validation_stats = trend.get("validation_stats", {})
        num_strict_touches = validation_stats.get("num_strict_touches", "N/A")
        num_breaches = validation_stats.get("num_breaches", "N/A")
        respect_ratio = validation_stats.get("respect_ratio", "N/A")
        num_body_penetrations = validation_stats.get("num_body_penetrations", "N/A")

        if trend.get("source") == "support": 
            print(f"--- Debugging Support Trendline ({timeframe}) ---")
            print(f"Trend Points Used for Fit: {trend["points"]}")
            print(f"Slope: {slope:.4f}, Intercept: {intercept:.4f}, R-squared (pivots): {trend.get("r_squared", float("nan")):.4f}")
            print(f"Score: {total_score if isinstance(total_score, str) else f'{total_score:.2f}'}")
            print(f"  Validation - Strict Touches: {num_strict_touches}, Breaches: {num_breaches}, Body Pen: {num_body_penetrations}, Respect Ratio: {respect_ratio if isinstance(respect_ratio, str) else f'{respect_ratio:.2f}'}")
            print(f"  Score Details - StrictT: {score_details.get("score_strict_touches",0):.0f}, RespectR: {score_details.get("score_respect_ratio",0):.0f}, RecencyS: {score_details.get("score_recency_strict",0):.0f}, R2: {score_details.get("score_r_squared_pivots",0):.0f}, BodyP: {score_details.get("penalty_body_penetration",0):.0f}, BreachP: {score_details.get("penalty_breach",0):.0f}, Slope: {score_details.get("slope_degrees",0):.1f}({score_details.get("slope_angle_score",0):.0f})")
            print(f"Current DF Index: {current_idx}")
            print(f"Calculated Trend Value at Current DF Index: {trend_value:.4f}")
            print(f"Current Price: {current_price_val}, Current Low: {current_low}, Current High: {current_high}")
            print(f"Distance to Trend: {distance}")
            print("---------------------------------------------")

        position_text = ""
        icon = ""
        # Logic changed to reflect trendline's position relative to price
        if current_low <= trend_value <= current_high:
            position_text = f"touching ({current_price_val:.2f})"
            icon = "✋"
        elif abs(current_price_val - trend_value) <= 5.0:
            position_text = f"at {current_price_val:.2f}"
            icon = "🟰"
        elif trend_value > current_price_val:  # Trendline is ABOVE current price
            position_text = "above"
            icon = "🔺"
        else:  # Trendline is BELOW current price (trend_value < current_price_val)
            position_text = "below"
            icon = "🔻"

        trend["trendline_value"] = round(trend_value, 2)
        trend["distance"] = distance
        trend["position_text"] = position_text
        trend["icon"] = icon
        trend["timeframe"] = timeframe
        trend["role"] = role
        trend["touch_points"] = [f"{p[1]:.2f}" for p in trend["points"]]
        return trend

    if support_trend:
        role = classify_trendline(df, support_trend, timeframe=timeframe)
        enriched = enrich_trend(support_trend, role, current_price)
        vectors["Support"] = enriched
        color = "🟩" if "Support" in role else "🟥"
        message = f"{color} {role} trendline detected ({timeframe})\n  • Position: {enriched["icon"]} {enriched["position_text"]}\n  • Distance: {enriched["distance"]} pts\n  • Touch points: {", ".join(enriched["touch_points"])}"
        messages.append(message)

    if resistance_trend:
        role = classify_trendline(df, resistance_trend, timeframe=timeframe)
        enriched = enrich_trend(resistance_trend, role, current_price)
        vectors["Resistance"] = enriched
        color = "🟩" if "Support" in role else "🟥" 
        message = f"{color} {role} trendline detected ({timeframe})\n  • Position: {enriched["icon"]} {enriched["position_text"]}\n  • Distance: {enriched["distance"]} pts\n  • Touch points: {", ".join(enriched["touch_points"])}"
        messages.append(message)

    if not messages:
        messages.append(f"No active trendline near current price ({timeframe})")
    return {"messages": messages, "vectors": vectors}
