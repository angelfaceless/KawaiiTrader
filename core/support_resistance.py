import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN

def detect_support_resistance(
    df: pd.DataFrame,
    window: int = 20,
    min_bounces: int = 2,
    min_reversal_atr: float = 1.5,
    atr_multiplier: float = 0.5,
    use_volume: bool = True,
    use_volume_profile: bool = True,
    volume_bins: int = 100,
):
    """
    Enhanced Support/Resistance detection with:
    - Dynamic ATR-based tolerance
    - DBSCAN clustering for significant zones
    - Optional volume profile injection
    """

    if len(df) < window + 15:
        return [], []

    highs = df["high"]
    lows = df["low"]
    closes = df["close"]
    opens = df["open"]
    volumes = df["volume"]

    prev_close = closes.shift(1)
    tr = pd.concat([
        highs - lows,
        (highs - prev_close).abs(),
        (lows - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean().bfill()

    support_candidates = []
    resistance_candidates = []

    for i in range(window, len(df)):
        slice_df = df.iloc[i - window:i]
        current_atr = atr.iloc[i]
        current_price = closes.iloc[i]

        if current_price == 0:
            continue

        dynamic_tolerance = atr_multiplier * current_atr / current_price
        level_high = slice_df['high'].max()
        level_low = slice_df['low'].min()

        if level_low == 0 or level_high == 0:
            continue

        # Support
        bounces = 0
        body_rejected = False
        for j in range(i - window, i):
            if abs(df["low"].iloc[j] - level_low) / level_low < dynamic_tolerance:
                bounces += 1
                if df["close"].iloc[j] > df["open"].iloc[j]:
                    body_rejected = True

        reversed_up = (closes.iloc[i] - level_low) > (current_atr * min_reversal_atr)

        vol_ok = True
        if use_volume:
            local_vol = volumes.iloc[i - window:i]
            adj_volume = volumes.iloc[i]
            mean_volume = local_vol.mean()
            vol_ok = adj_volume > mean_volume * 1.5

        if bounces >= min_bounces and body_rejected and reversed_up and vol_ok:
            support_candidates.append(level_low)

        # Resistance
        bounces = 0
        body_rejected = False
        for j in range(i - window, i):
            if abs(df["high"].iloc[j] - level_high) / level_high < dynamic_tolerance:
                bounces += 1
                if df["close"].iloc[j] < df["open"].iloc[j]:
                    body_rejected = True

        reversed_down = (level_high - closes.iloc[i]) > (current_atr * min_reversal_atr)

        vol_ok = True
        if use_volume:
            local_vol = volumes.iloc[i - window:i]
            adj_volume = volumes.iloc[i]
            mean_volume = local_vol.mean()
            vol_ok = adj_volume > mean_volume * 1.5

        if bounces >= min_bounces and body_rejected and reversed_down and vol_ok:
            resistance_candidates.append(level_high)

    def dbscan_cluster(levels, eps_ratio=0.0015, min_samples=1):
        if not levels:
            return []
        levels = np.array(levels).reshape(-1, 1)
        eps = np.mean(levels) * eps_ratio
        clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(levels)
        result = []
        for label in set(clustering.labels_):
            if label == -1:
                continue
            cluster_points = levels[clustering.labels_ == label]
            result.append(round(cluster_points.mean(), 2))
        return sorted(result)

    current_price = closes.iloc[-1]
    support_levels = [s for s in dbscan_cluster(support_candidates) if s < current_price]
    resistance_levels = [r for r in dbscan_cluster(resistance_candidates) if r > current_price]

    if use_volume_profile:
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        bin_edges = np.linspace(df["low"].min(), df["high"].max(), volume_bins)
        volume_profile = pd.Series(0.0, index=bin_edges)

        for price, volume in zip(typical_price, volumes):
            idx = volume_profile.index.get_indexer([price], method='nearest')[0]
            idx = np.clip(idx, 0, len(volume_profile) - 1)
            volume_profile.iloc[idx] += volume

        hvn_threshold = volume_profile.mean() + volume_profile.std()
        lvn_threshold = volume_profile.mean() - volume_profile.std()

        hvn_levels = volume_profile[volume_profile > hvn_threshold].index.tolist()
        lvn_levels = volume_profile[volume_profile < lvn_threshold].index.tolist()

        support_levels += [lvl for lvl in lvn_levels if lvl < current_price]
        resistance_levels += [lvl for lvl in hvn_levels if lvl > current_price]

        support_levels = dbscan_cluster(support_levels)
        resistance_levels = dbscan_cluster(resistance_levels)

    return support_levels, resistance_levels
