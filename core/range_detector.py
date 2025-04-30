# kawaiitrader/core/range_detector.py

import pandas as pd

def detect_body_range(df: pd.DataFrame, timeframe: str = "1h"):
    """
    Detects the current price range using candle bodies (open/close only).
    
    Args:
        df (pd.DataFrame): OHLCV data.
        timeframe (str): '15m', '1h', '4h', etc.

    Returns:
        dict with range_high, range_low, and a description string
    """
    tf_window_map = {
        "15m": 96,     # ~1 day
        "30m": 48,
        "1h": 50,
        "4h": 30,
        "1d": 15
    }

    window = tf_window_map.get(timeframe, 50)

    if len(df) < window:
        raise ValueError(f"Not enough data for {window}-bar range detection.")

    body_highs = df[['open', 'close']].max(axis=1)
    body_lows = df[['open', 'close']].min(axis=1)

    recent_high = round(body_highs[-window:].max(), 2)
    recent_low = round(body_lows[-window:].min(), 2)

    return {
        "range_high": recent_high,
        "range_low": recent_low,
        "message": f"Range (body-only) over last {window} bars: {recent_low} – {recent_high}"
    }
