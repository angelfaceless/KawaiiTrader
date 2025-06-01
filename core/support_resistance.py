import pandas as pd
import numpy as np

def detect_support_resistance(
    df: pd.DataFrame,
    window: int = 20,
    tolerance: float = 0.002,
    min_bounces: int = 2,
    min_reversal_atr: float = 1.5,
    use_volume: bool = True,
    use_volume_profile: bool = True,
    volume_bins: int = 100
):
    """
    Detects high-confidence support/resistance zones based on:
    - Wick + body bounce filtering
    - ATR-based reversal strength
    - ATR-normalized volume spike filtering
    - Optional Volume Profile HVN/LVN injection
    - Clustering logic to reduce noise
    - Filters supports below and resistances above current price
    """

    # === Extract Columns ===
    highs = df["high"]
    lows = df["low"]
    closes = df["close"]
    opens = df["open"]
    volumes = df["volume"]

    # === ATR via True Range ===
    prev_close = closes.shift(1)
    tr = pd.concat([
        highs - lows,
        (highs - prev_close).abs(),
        (lows - prev_close).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(window=14).mean().fillna(method="backfill")

    potential_supports = []
    potential_resistances = []

    for i in range(window, len(df)):
        slice_df = df.iloc[i - window:i]
        current_atr = atr.iloc[i]
        level_high = slice_df[['open', 'close']].max(axis=1).max()
        level_low = slice_df[['open', 'close']].min(axis=1).min()

        # === Support Detection ===
        support_bounces = 0
        support_body_rejected = False
        for j in range(i - window, i):
            if abs(df["low"].iloc[j] - level_low) / level_low < tolerance:
                support_bounces += 1
                if df["close"].iloc[j] > df["open"].iloc[j]:  # bullish body rejection
                    support_body_rejected = True

        reversed_up = (df["close"].iloc[i] - level_low) > (current_atr * min_reversal_atr)

        volume_ok = True
        if use_volume:
            local_vol = volumes.iloc[i - window:i]
            local_atr = atr.iloc[i - window:i]
            adj_volume = volumes.iloc[i] / current_atr
            mean_adj_volume = (local_vol / local_atr).mean()
            volume_ok = adj_volume > mean_adj_volume * 1.5

        if support_bounces >= min_bounces and support_body_rejected and reversed_up and volume_ok:
            potential_supports.append(round(level_low, 2))

        # === Resistance Detection ===
        resistance_bounces = 0
        resistance_body_rejected = False
        for j in range(i - window, i):
            if abs(df["high"].iloc[j] - level_high) / level_high < tolerance:
                resistance_bounces += 1
                if df["close"].iloc[j] < df["open"].iloc[j]:  # bearish body rejection
                    resistance_body_rejected = True

        reversed_down = (level_high - df["close"].iloc[i]) > (current_atr * min_reversal_atr)

        volume_ok = True
        if use_volume:
            local_vol = volumes.iloc[i - window:i]
            local_atr = atr.iloc[i - window:i]
            adj_volume = volumes.iloc[i] / current_atr
            mean_adj_volume = (local_vol / local_atr).mean()
            volume_ok = adj_volume > mean_adj_volume * 1.5

        if resistance_bounces >= min_bounces and resistance_body_rejected and reversed_down and volume_ok:
            potential_resistances.append(round(level_high, 2))

    def cluster(levels):
        clustered = []
        for level in sorted(set(levels)):
            if not clustered or all(abs(level - x) / x > tolerance for x in clustered):
                clustered.append(level)
        return clustered

    current_price = df["close"].iloc[-1]
    support_levels = [s for s in cluster(potential_supports) if s < current_price]
    resistance_levels = [r for r in cluster(potential_resistances) if r > current_price]

    # === Volume Profile HVN/LVN Injection ===
    if use_volume_profile:
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        bin_edges = np.linspace(df["low"].min(), df["high"].max(), volume_bins)
        volume_profile = pd.Series(0.0, index=bin_edges)

        for price, volume in zip(typical_price, volumes):
            idx = volume_profile.index.get_indexer([price], method='nearest')[0]
            volume_profile.iloc[idx] += volume

        hvn_threshold = volume_profile.mean() + volume_profile.std()
        lvn_threshold = volume_profile.mean() - volume_profile.std()

        hvn_levels = volume_profile[volume_profile > hvn_threshold].index.tolist()
        lvn_levels = volume_profile[volume_profile < lvn_threshold].index.tolist()

        for level in hvn_levels:
            if level < current_price:
                support_levels.append(round(level, 2))
            else:
                resistance_levels.append(round(level, 2))

        for level in lvn_levels:
            if level < current_price:
                support_levels.append(round(level, 2))
            else:
                resistance_levels.append(round(level, 2))

        support_levels = cluster(support_levels)
        resistance_levels = cluster(resistance_levels)

    return support_levels, resistance_levels
