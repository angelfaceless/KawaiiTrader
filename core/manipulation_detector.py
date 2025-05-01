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
            - 'returned_to_range': bool
    """
    last_candle = df.iloc[-1]

    high = last_candle["high"]
    low = last_candle["low"]
    close = last_candle["close"]

    # Upside manipulation
    if high > range_high:
        returned = close <= range_high
        return {
            "manipulated": True,
            "direction": "up",
            "returned_to_range": returned,
            "message": (
                f"🟨 Manipulation Detected: Price wicked above {range_high} "
                f"and {'returned' if returned else 'did NOT return'} inside range."
            )
        }

    # Downside manipulation
    if low < range_low:
        returned = close >= range_low
        return {
            "manipulated": True,
            "direction": "down",
            "returned_to_range": returned,
            "message": (
                f"🟨 Manipulation Detected: Price wicked below {range_low} "
                f"and {'returned' if returned else 'did NOT return'} inside range."
            )
        }

    return {
        "manipulated": False,
        "direction": None,
        "returned_to_range": False,
        "message": "No manipulation detected."
    }
