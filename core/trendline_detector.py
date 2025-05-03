import numpy as np
import pandas as pd
from scipy.stats import linregress


def detect_pivots(df, window=5):
    highs = df["high"]
    lows = df["low"]
    pivot_highs = []
    pivot_lows = []

    for i in range(window, len(df) - window):
        if highs[i] == max(highs[i - window:i + window + 1]):
            pivot_highs.append((i, highs[i]))
        if lows[i] == min(lows[i - window:i + window + 1]):
            pivot_lows.append((i, lows[i]))

    return pivot_highs, pivot_lows


def fit_trendline(points, kind="support", r_threshold=0.85):
    if len(points) < 3:
        return None

    x = np.array([pt[0] for pt in points])
    y = np.array([pt[1] for pt in points])
    slope, intercept, r_value, _, _ = linregress(x, y)

    if abs(r_value) < r_threshold:
        return None

    return slope, intercept


def classify_trendline(df, slope, intercept):
    latest_idx = len(df) - 1
    current_price = df["close"].iloc[-1]
    trend_value = slope * latest_idx + intercept

    if current_price >= trend_value:
        return "Support"
    else:
        return "Resistance"


def detect_trendline(df: pd.DataFrame, timeframe: str = "1h", symbol: str = "ES"):
    pivot_highs, pivot_lows = detect_pivots(df)

    support_trend = fit_trendline(pivot_lows, "support")
    resistance_trend = fit_trendline(pivot_highs, "resistance")

    messages = []
    vectors = {}

    if support_trend:
        role = classify_trendline(df, *support_trend)
        if role == "Support":
            vectors["Support"] = support_trend
            levels = [f"{lvl:.2f}" for _, lvl in pivot_lows]
            messages.append(f"🟩 Support trendline detected ({timeframe})")
            messages.append(f"    Touch points: {', '.join(levels)}")

    if resistance_trend:
        role = classify_trendline(df, *resistance_trend)
        if role == "Resistance":
            vectors["Resistance"] = resistance_trend
            levels = [f"{lvl:.2f}" for _, lvl in pivot_highs]
            messages.append(f"🟥 Resistance trendline detected ({timeframe})")
            messages.append(f"    Touch points: {', '.join(levels)}")

    if not messages:
        messages.append(f"No active trendline near current price ({timeframe})")

    return {
        "messages": messages,
        "vectors": vectors
    }
