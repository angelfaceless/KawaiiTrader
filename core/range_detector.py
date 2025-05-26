import pandas as pd
import numpy as np


def _volume_profile_score(prices: np.ndarray, volumes: np.ndarray, bins: int = 100) -> float:
    """
    Score: top-2 volume bins as % of total volume.
    """
    if len(prices) == 0 or volumes.sum() == 0:
        return 0.0

    hist, _ = np.histogram(prices, bins=bins, weights=volumes)
    if hist.sum() == 0:
        return 0.0

    top_two = np.sort(hist)[-2:]
    return float(top_two.sum() / hist.sum())


def detect_consolidation_hybrid(
    df: pd.DataFrame,
    window: int = 50,
    atr_multiplier: float = 1.5,
    tolerance_pct: float = 0.02,
    min_bounces: int = 1,
    *,
    use_body: bool = True,
    require_both: bool = False,
    volume_profile_threshold: float = 0.1
) -> dict:
    if df is None or df.empty or len(df) < window:
        return {
            "range_low": np.nan,
            "range_high": np.nan,
            "message": f"Not enough data to detect consolidation (requires {window} candles).",
            "is_range": False
        }

    recent = df[-window:]

    if use_body:
        hi_series = recent[["open", "close"]].max(axis=1)
        lo_series = recent[["open", "close"]].min(axis=1)
    else:
        hi_series = recent["high"]
        lo_series = recent["low"]

    high = hi_series
    low = lo_series
    close = recent["close"]

    tr = pd.concat([
        recent["high"] - recent["low"],
        (recent["high"] - recent["close"].shift()).abs(),
        (recent["low"] - recent["close"].shift()).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window).mean().iloc[-1]

    range_high = high.max()
    range_low = low.min()
    range_width = range_high - range_low
    tolerance = range_width * tolerance_pct

    low_touches = ((recent["low"] - range_low).abs() <= tolerance).sum()
    high_touches = ((recent["high"] - range_high).abs() <= tolerance).sum()

    is_tight = range_width < atr * atr_multiplier
    is_bouncing = (low_touches >= min_bounces) and (high_touches >= min_bounces)

    vp_score = _volume_profile_score(
        prices=recent["close"].values.astype(float),
        volumes=recent["volume"].values.astype(float)
    )
    vp_ok = vp_score >= volume_profile_threshold

    if require_both:
        primary_ok = is_tight and is_bouncing
    else:
        primary_ok = is_tight or is_bouncing

    is_range = primary_ok and vp_ok

    if is_range:
        msg = (
            f"Consolidation zone detected from {range_low:.2f} to {range_high:.2f} | "
            f"{low_touches} low wicks / {high_touches} high wicks | "
            f"ATR={atr:.2f} | VP Score={vp_score:.2f}"
        )
    else:
        msg = (
            f"No consolidation zone detected. "
            f"(tight={is_tight}, bounce={is_bouncing}, vp_ok={vp_ok}, vp_score={vp_score:.2f})"
        )

    return {
        "range_low": float(range_low),
        "range_high": float(range_high),
        "low_touches": int(low_touches),
        "high_touches": int(high_touches),
        "vp_score": float(vp_score),
        "atr": float(atr),
        "message": msg,
        "is_range": is_range
    }


def detect_body_range(df: pd.DataFrame, timeframe: str) -> dict:
    return detect_consolidation_hybrid(
        df,
        window=50,
        atr_multiplier=1.5,
        tolerance_pct=0.02,
        min_bounces=1,
        use_body=True,
        require_both=False,
        volume_profile_threshold=0.1
    )
