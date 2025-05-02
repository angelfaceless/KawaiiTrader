import pandas as pd
import numpy as np
from core.range_detector import detect_body_range as detect_range

def detect_manipulation(df: pd.DataFrame, timeframe: str = "15m", lookback: int = 20, lookahead: int = 30, momentum_multiplier: float = 1.5):
    df = df.copy()
    df['body_size'] = abs(df['close'] - df['open'])
    df['avg_body_size'] = df['body_size'].rolling(window=lookback).mean()
    df['is_momentum'] = df['body_size'] > (df['avg_body_size'] * momentum_multiplier)

    range_info = detect_range(df, timeframe)

    if not isinstance(range_info, dict) or 'range_high' not in range_info or 'range_low' not in range_info:
        raise ValueError("Expected range_info to be a dict with 'range_high' and 'range_low' keys.")

    current_range_high = range_info['range_high']
    current_range_low = range_info['range_low']

    manipulations = []
    breakouts = []

    for i in range(1, len(df)):
        candle = df.iloc[i]
        timestamp = candle.name
        close = candle['close']
        open_ = candle['open']
        is_momentum = candle['is_momentum']
        body_high = max(open_, close)
        body_low = min(open_, close)

        if body_low > current_range_high and is_momentum:
            breakouts.append({"timestamp": timestamp, "price": close, "direction": "bullish"})
        elif body_high < current_range_low and is_momentum:
            breakouts.append({"timestamp": timestamp, "price": close, "direction": "bearish"})
        elif (body_high > current_range_high or body_low < current_range_low) and current_range_low <= close <= current_range_high:
            direction = "bullish" if body_low < current_range_low else "bearish"
            manipulations.append({"timestamp": timestamp, "price": close, "direction": direction})

    msg = f"Detected {len(manipulations)} manipulations and {len(breakouts)} breakouts based on full-body momentum logic."
    status = "manipulated" if len(manipulations) > 0 or len(breakouts) > 0 else "clean"

    # ✅ Safe directional bias calculation using .get()
    total_bullish = sum(1 for m in manipulations + breakouts if m.get('direction') == "bullish")
    total_bearish = sum(1 for m in manipulations + breakouts if m.get('direction') == "bearish")

    if total_bullish > total_bearish:
        bias = "bullish"
    elif total_bearish > total_bullish:
        bias = "bearish"
    else:
        bias = "neutral"

    return {
        "manipulations": manipulations,
        "breakouts": breakouts,
        "message": msg,
        "status": status,
        "bias": bias
    }
