import pandas as pd
import numpy as np


def detect_consolidation_hybrid(
    df: pd.DataFrame,
    window: int = 50,
    atr_multiplier: float = 1.25,
    tolerance_pct: float = 0.015,
    min_bounces: int = 1
) -> dict:
    """
    Hybrid consolidation detection:
    - ATR-based compression
    - Wick bounce logic (highs/lows)
    - Passes if either condition is met
    """
    if df is None or df.empty or len(df) < window:
        return {
            "range_low": np.nan,
            "range_high": np.nan,
            "message": f"Not enough data to detect consolidation (requires {window} candles).",
            "is_range": False
        }

    recent = df[-window:]
    high = recent["high"]
    low = recent["low"]
    close = recent["close"]

    # ATR
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(window).mean().iloc[-1]

    range_high = high.max()
    range_low = low.min()
    range_width = range_high - range_low
    tolerance = range_width * tolerance_pct

    # Wick-based touch logic
    low_touches = ((recent["low"] - range_low).abs() <= tolerance).sum()
    high_touches = ((recent["high"] - range_high).abs() <= tolerance).sum()

    is_tight = range_width < atr * atr_multiplier
    is_bouncing = low_touches >= min_bounces and high_touches >= min_bounces
    is_range = is_tight or is_bouncing

    if is_range:
        msg = (
            f"Consolidation zone detected from {range_low:.2f} to {range_high:.2f} "
            f"({low_touches} low wicks, {high_touches} high wicks, ATR={atr:.2f})."
        )
    else:
        msg = "No consolidation zone detected recently."

    return {
        "range_low": float(range_low),
        "range_high": float(range_high),
        "low_touches": int(low_touches),
        "high_touches": int(high_touches),
        "message": msg,
        "is_range": is_range
    }


def detect_body_range(df: pd.DataFrame, timeframe: str) -> dict:
    """
    Entry point used by analyzer.py.
    """
    return detect_consolidation_hybrid(
        df,
        window=50,
        atr_multiplier=1.25,
        tolerance_pct=0.015,
        min_bounces=1
    )
