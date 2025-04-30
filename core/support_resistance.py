# kawaiitrader/core/support_resistance.py

import pandas as pd

def detect_support_resistance(df: pd.DataFrame, window: int = 20, tolerance: float = 0.002):
    """
    Identifies support and resistance levels using candle body closes over a rolling window.
    
    Args:
        df (pd.DataFrame): OHLCV data with 'close' column.
        window (int): Number of bars to use in rolling window.
        tolerance (float): Minimum % difference to separate levels.

    Returns:
        (support_levels, resistance_levels): Two lists of float levels.
    """
    body_highs = df[['open', 'close']].max(axis=1)
    body_lows = df[['open', 'close']].min(axis=1)

    supports = []
    resistances = []

    for i in range(window, len(df)):
        range_slice = df.iloc[i - window:i]
        local_high = range_slice[['open', 'close']].max(axis=1).max()
        local_low = range_slice[['open', 'close']].min(axis=1).min()

        # Avoid adding levels too close to existing ones
        if not any(abs(local_high - r) / r < tolerance for r in resistances):
            resistances.append(round(local_high, 2))

        if not any(abs(local_low - s) / s < tolerance for s in supports):
            supports.append(round(local_low, 2))

    return supports, resistances
