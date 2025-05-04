import pandas as pd
import numpy as np

def detect_support_resistance(
    df: pd.DataFrame,
    window: int = 20,
    tolerance: float = 0.002,
    min_bounces: int = 2,
    min_reversal_atr: float = 1.5,
    use_volume: bool = True
):
    """
    Detects high-confidence support/resistance zones based on:
    - Wick + body bounce filtering
    - ATR-based reversal strength
    - Optional volume spike confirmation
    - Clustering logic to reduce noise

    Returns:
        (support_levels, resistance_levels): Cleaned key price levels
    """
    highs = df["high"]
    lows = df["low"]
    closes = df["close"]
    opens = df["open"]
    volumes = df["volume"]

    atr = (highs - lows).rolling(window=14).mean()

    potential_supports = []
    potential_resistances = []

    for i in range(window, len(df)):
        slice_df = df.iloc[i - window:i]
        current_atr = atr.iloc[i]
        level_high = slice_df[['open', 'close']].max(axis=1).max()
        level_low = slice_df[['open', 'close']].min(axis=1).min()

        # -- Filter: Wick touches and reversal bounce from LOW --
        support_bounces = 0
        support_body_rejected = False
        for j in range(i - window, i):
            if abs(df["low"].iloc[j] - level_low) / level_low < tolerance:
                support_bounces += 1
                if df["close"].iloc[j] > df["open"].iloc[j]:  # body rejection upward
                    support_body_rejected = True

        reversed_up = (df["close"].iloc[i] - level_low) > (current_atr * min_reversal_atr)

        volume_ok = True
        if use_volume:
            local_vol = volumes.iloc[i - window:i]
            volume_ok = volumes.iloc[i] > local_vol.mean() * 1.5

        if support_bounces >= min_bounces and support_body_rejected and reversed_up and volume_ok:
            potential_supports.append(round(level_low, 2))

        # -- Filter: Wick touches and reversal bounce from HIGH --
        resistance_bounces = 0
        resistance_body_rejected = False
        for j in range(i - window, i):
            if abs(df["high"].iloc[j] - level_high) / level_high < tolerance:
                resistance_bounces += 1
                if df["close"].iloc[j] < df["open"].iloc[j]:  # body rejection downward
                    resistance_body_rejected = True

        reversed_down = (level_high - df["close"].iloc[i]) > (current_atr * min_reversal_atr)

        volume_ok = True
        if use_volume:
            local_vol = volumes.iloc[i - window:i]
            volume_ok = volumes.iloc[i] > local_vol.mean() * 1.5

        if resistance_bounces >= min_bounces and resistance_body_rejected and reversed_down and volume_ok:
            potential_resistances.append(round(level_high, 2))

    def cluster(levels):
        clustered = []
        for level in sorted(set(levels)):
            if not clustered or all(abs(level - x) / x > tolerance for x in clustered):
                clustered.append(level)
        return clustered

    support_levels = cluster(potential_supports)
    resistance_levels = cluster(potential_resistances)

    return support_levels, resistance_levels
