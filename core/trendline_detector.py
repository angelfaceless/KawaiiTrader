# kawaiitrader/core/trendline_detector.py

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, RANSACRegressor

def detect_pivots(df: pd.DataFrame, window_sizes=[3, 5, 7]):
    """
    Detect pivot highs and lows based on candle bodies.
    """
    body_highs = df[['open', 'close']].max(axis=1)
    body_lows = df[['open', 'close']].min(axis=1)

    pivot_highs = []
    pivot_lows = []

    for w in window_sizes:
        for i in range(w, len(df) - w):
            window_slice = body_highs[i - w:i + w + 1]
            if df.index[i] == window_slice.idxmax():
                pivot_highs.append((i, window_slice.max()))
            
            window_slice = body_lows[i - w:i + w + 1]
            if df.index[i] == window_slice.idxmin():
                pivot_lows.append((i, window_slice.min()))

    return pivot_highs, pivot_lows

def fit_trendline(points, kind="support"):
    """
    Fit a linear or RANSAC regression trendline to a list of pivot points.
    """
    if len(points) < 2:
        return None

    x = np.array([p[0] for p in points]).reshape(-1, 1)
    y = np.array([p[1] for p in points])

    try:
        model = RANSACRegressor()
        model.fit(x, y)
        slope = model.estimator_.coef_[0]
        intercept = model.estimator_.intercept_
        return slope, intercept
    except Exception:
        return None

def classify_trendline(df: pd.DataFrame, slope, intercept):
    """
    Determine if the trendline acts as support or resistance at the current price.
    """
    current_index = len(df) - 1
    current_price = df.iloc[-1]["close"]
    trendline_value = slope * current_index + intercept

    if current_price > trendline_value:
        return "Support"
    elif current_price < trendline_value:
        return "Resistance"
    else:
        return "Touching"

def detect_trendline(df: pd.DataFrame, timeframe: str = "1h"):
    pivot_highs, pivot_lows = detect_pivots(df)

    support_trend = fit_trendline(pivot_lows, "support")
    resistance_trend = fit_trendline(pivot_highs, "resistance")

    results = []

    if support_trend:
        role = classify_trendline(df, *support_trend)
        if role == "Support":
            results.append(f"🟩 Support trendline detected ({timeframe})")

    if resistance_trend:
        role = classify_trendline(df, *resistance_trend)
        if role == "Resistance":
            results.append(f"🟥 Resistance trendline detected ({timeframe})")

    if not results:
        results.append(f"No active trendline near current price ({timeframe})")

    return results
