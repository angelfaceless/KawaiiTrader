# utils/htfcontext_helper.py

from typing import List, Dict, Literal
import pandas as pd
from core.support_resistance import detect_support_resistance
from core.trendline_detector import detect_trendline
from data.databento_client import fetch_ohlcv, get_dynamic_lookback

ConfidenceLevel = Literal["strong", "medium", "weak"]

def get_higher_timeframes(base_timeframe: str) -> list[str]:
    hierarchy_map = {
        "1min": ["5min", "15min"],
        "5min": ["15min", "1h"],
        "15min": ["1h", "4h"],
        "1h": ["4h", "1d"],
        "4h": ["1d"],
        "1d": []
    }
    always_include = {"4h", "1d"}
    dynamic = set(hierarchy_map.get(base_timeframe, []))
    combined = dynamic.union(always_include)
    combined.discard(base_timeframe)  # ✅ Prevent self-comparison
    tf_order = ["1min", "5min", "15min", "1h", "4h", "1d", "1w", "1mo"]
    return sorted(combined, key=lambda tf: tf_order.index(tf) if tf in tf_order else 999)

def compute_matches(level: float, htf_levels_by_tf: Dict[str, List[float]], atr: float, tolerance_ratio: float = 0.10):
    tolerance = atr * tolerance_ratio
    matched_tfs = []
    for tf, levels in htf_levels_by_tf.items():
        if any(abs(level - l) <= tolerance for l in levels):
            matched_tfs.append(tf)
    return matched_tfs

def compare_levels_with_htf(
    symbol_details: dict,
    base_timeframe: str,
    base_df: pd.DataFrame,
    base_supports: List[float],
    base_resistances: List[float],
    base_trendlines: Dict
) -> Dict[str, Dict[str | float, Dict]]:
    confidence = {
        "support": {},
        "resistance": {},
        "trendline": {}
    }

    atr = (base_df["high"] - base_df["low"]).rolling(window=14).mean().iloc[-1]
    htf_timeframes = get_higher_timeframes(base_timeframe)

    htf_supps_by_tf = {}
    htf_ress_by_tf = {}
    htf_trendlines = []

    for tf in htf_timeframes:
        lookback = get_dynamic_lookback(tf)
        df_htf = fetch_ohlcv(symbol_details, tf, lookback_days=lookback)
        if df_htf is None or df_htf.empty:
            continue

        s, r = detect_support_resistance(df_htf)
        htf_supps_by_tf[tf] = s
        htf_ress_by_tf[tf] = r

        trend = detect_trendline(df_htf, tf, symbol_details["input_symbol"])
        for role, tr in trend["vectors"].items():
            slope, intercept = tr["slope"], tr["intercept"]
            htf_trendlines.append((slope, intercept, tf))

    # SUPPORT/RESISTANCE
    for s in base_supports:
        matched = compute_matches(s, htf_supps_by_tf, atr)
        lvl = "strong" if len(matched) >= 2 else "medium" if len(matched) == 1 else "weak"
        confidence["support"][s] = {"level": lvl, "matched_timeframes": matched}

    for r in base_resistances:
        matched = compute_matches(r, htf_ress_by_tf, atr)
        lvl = "strong" if len(matched) >= 2 else "medium" if len(matched) == 1 else "weak"
        confidence["resistance"][r] = {"level": lvl, "matched_timeframes": matched}

    # TRENDLINES
    for role, tr in base_trendlines.items():
        matched_tfs = []
        for slope2, intercept2, tf in htf_trendlines:
            slope1, intercept1 = tr["slope"], tr["intercept"]
            if slope1 == 0 or slope2 == 0:
                continue
            slope_ratio = min(abs(slope1 / slope2), abs(slope2 / slope1))
            slope_match = 0.90 <= slope_ratio <= 1.10
            price_diff = abs(intercept1 - intercept2)
            if slope_match and price_diff <= atr * 2:
                matched_tfs.append(tf)

        lvl = "strong" if len(matched_tfs) >= 2 else "medium" if len(matched_tfs) == 1 else "weak"
        confidence["trendline"][role] = {"level": lvl, "matched_timeframes": matched_tfs}

    return confidence
