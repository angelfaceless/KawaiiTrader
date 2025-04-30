# kawaiitrader/core/manipulation_detector.py

import pandas as pd

def detect_manipulation(df: pd.DataFrame, range_low: float, range_high: float) -> dict:
    """
    Detects if price has wicked outside the range and closed back inside.

    Args:
        df (pd.DataFrame): OHLCV data.
        range_low (float): Lower body range bound.
        range_high (float): Upper body range bound.

    Returns:
        dict with keys:
            - 'manipulated': bool
            - 'direction': 'up' | 'down' | None
            - 'message': str
    """
    last_candle = df.iloc[-1]

    high = last_candle["high"]
    low = last_candle["low"]
    close = last_candle["close"]

    # Check for upside wick manipulation
    if high > range_high and close <= range_high:
        return {
            "manipulated": True,
            "direction": "up",
            "message": f"🟨 Manipulation Detected: Price wicked above {range_high} and closed back inside range."
        }

    # Check for downside wick manipulation
    if low < range_low and close >= range_low:
        return {
            "manipulated": True,
            "direction": "down",
            "message": f"🟨 Manipulation Detected: Price wicked below {range_low} and closed back inside range."
        }

    return {
        "manipulated": False,
        "direction": None,
        "message": "No manipulation detected."
    }
