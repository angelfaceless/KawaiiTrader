import numpy as np
import pandas as pd
from scipy.stats import linregress


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


def fit_trendline(points, kind="support", r_threshold=0.85):
    if len(points) < 3:
        return None

    x_raw = np.array([pt[0] for pt in points])
    y = np.array([pt[1] for pt in points])
    x = x_raw - x_raw[0]
    slope, intercept, r_value, _, _ = linregress(x, y)

    if abs(r_value) < r_threshold:
        return None

    return {
        "slope": slope,
        "intercept": intercept,
        "start_index": x_raw[0],
        "points": points,
        "source": kind  # 'support' or 'resistance'
    }


def classify_trendline(df, trend_meta, timeframe="1h"):
    slope = trend_meta["slope"]
    intercept = trend_meta["intercept"]
    start_idx = trend_meta["start_index"]

    tf_map = {
        "1min": 1440, "5min": 288, "15min": 96, "30min": 48,
        "1h": 24, "2h": 12, "3h": 8, "4h": 6, "6h": 4,
        "12h": 2, "1d": 1,
    }

    candles_per_day = tf_map.get(timeframe.lower(), 24)
    lookback = min(3 * candles_per_day, len(df))

    recent_df = df.tail(lookback)
    closes = recent_df["close"].values
    x_vals = np.arange(len(df) - lookback, len(df)) - start_idx
    trend_values = slope * x_vals + intercept

    above_ratio = np.mean(closes > trend_values)
    below_ratio = np.mean(closes < trend_values)

    if above_ratio > 0.7:
        return "Support"
    elif below_ratio > 0.7:
        return "Resistance"
    elif trend_meta["source"] == "resistance" and above_ratio > 0.4 and slope > 0:
        return "Support (flipped from resistance)"
    elif trend_meta["source"] == "support" and below_ratio > 0.4 and slope < 0:
        return "Resistance (flipped from support)"
    else:
        return "Ambiguous"


def detect_trendline(df: pd.DataFrame, timeframe: str = "1h", symbol: str = "ES"):
    pivot_highs, pivot_lows = detect_pivots(df)

    support_trend = fit_trendline(pivot_lows, "support")
    resistance_trend = fit_trendline(pivot_highs, "resistance")

    messages = []
    vectors = {}

    if support_trend:
        role = classify_trendline(df, support_trend, timeframe=timeframe)
        if "Support" in role:
            vectors["Support"] = support_trend
            levels = [f"{lvl:.2f}" for _, lvl in support_trend["points"]]
            messages.append(f"🟩 {role} trendline detected ({timeframe})")
            messages.append(f"    Touch points: {', '.join(levels)}")

    if resistance_trend:
        role = classify_trendline(df, resistance_trend, timeframe=timeframe)
        if "Resistance" in role or "flipped" in role:
            vectors["Resistance"] = resistance_trend
            levels = [f"{lvl:.2f}" for _, lvl in resistance_trend["points"]]
            messages.append(f"🟥 {role} trendline detected ({timeframe})")
            messages.append(f"    Touch points: {', '.join(levels)}")

    if not messages:
        messages.append(f"No active trendline near current price ({timeframe})")

    return {
        "messages": messages,
        "vectors": vectors
    }
