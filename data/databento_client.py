import os
import math
import pandas as pd
from datetime import datetime, timedelta, timezone

from databento import Historical
from dotenv import load_dotenv
from utils.symbols import resolve_symbol_alias

load_dotenv()
API_KEY = os.getenv("DATABENTO_API_KEY")

MAX_DATA_DELAY = timedelta(minutes=15)
MAX_AVAILABLE_END = datetime(2025, 5, 3, 0, 0, 0, tzinfo=timezone.utc)

TIMEFRAME_SECONDS = {
    "1min": 60,
    "5min": 300,
    "15min": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400
}

TIMEFRAME_MAP = {
    "1min": "1min",
    "5min": "5min",
    "15min": "15min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1d"
}

def get_dynamic_lookback(timeframe: str, target_candles: int = 80) -> int:
    seconds = TIMEFRAME_SECONDS.get(timeframe)
    if not seconds:
        return 2
    if timeframe == "1d":
        return math.ceil((target_candles / 5) * 7)
    return math.ceil((target_candles * seconds) / 86400)

def is_weekend(dt: datetime) -> bool:
    return dt.weekday() in (5, 6)

def fetch_ohlcv(symbol: str, timeframe: str = "15min", lookback_days: int = None) -> pd.DataFrame:
    user_input_symbol = symbol
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    minute_mod = now.minute % 15
    aligned_now = now - timedelta(minutes=minute_mod)
    end_time = aligned_now - MAX_DATA_DELAY
    if end_time > MAX_AVAILABLE_END:
        end_time = MAX_AVAILABLE_END

    if is_weekend(now) and lookback_days is None:
        lookback_days = 3

    start_time = end_time - timedelta(days=lookback_days or get_dynamic_lookback(timeframe))

    futures_roots = {"ES", "MES", "NQ", "MNQ", "RTY", "YM"}
    symbol_upper = symbol.upper()

    if symbol_upper in futures_roots:
        if is_weekend(now):
            fallback_contracts = {
                "ES": "ESM5",
                "MES": "MESM5",
                "NQ": "NQM5",
                "MNQ": "MNQM5",
                "RTY": "RTYM5",
                "YM": "YMM5"
            }
            final_symbol = fallback_contracts.get(symbol_upper, symbol_upper)
            stype = "raw_symbol"
        else:
            final_symbol = f"{symbol_upper}.c.0"
            stype = "continuous"
    else:
        final_symbol = resolve_symbol_alias(symbol_upper)
        is_equity = final_symbol.isalpha() and len(final_symbol) <= 5
        stype = "raw_symbol" if is_equity else "parent"

    dataset = (
        "XNAS.ITCH" if final_symbol.endswith("Q") or final_symbol in ["AAPL", "TSLA"]
        else "XNYS.ITCH" if stype == "raw_symbol" and final_symbol.isalpha()
        else "GLBX.MDP3"
    )

    client = Historical(key=API_KEY)

    try:
        data = client.timeseries.get_range(
            dataset=dataset,
            schema="ohlcv_1s",
            symbols=final_symbol,
            stype_in=stype,
            start=start_time,
            end=end_time,
        )
        df = data.to_df()
        if df is None or df.empty or "ts_event" not in df.columns:
            raise ValueError("ohlcv_1s missing or invalid")
    except Exception:
        data = client.timeseries.get_range(
            dataset=dataset,
            schema="trades",
            symbols=final_symbol,
            stype_in=stype,
            start=start_time,
            end=end_time,
        )
        if not data:
            return None
        df = data.to_df()
        if df is None or df.empty or "ts_event" not in df.columns:
            return None

    df["timestamp"] = pd.to_datetime(df["ts_event"], unit="ns")
    df.set_index("timestamp", inplace=True)

    if "price" in df.columns and "size" in df.columns:
        df = df[["price", "size"]].rename(columns={"price": "close", "size": "volume"})
        resample_str = TIMEFRAME_MAP.get(timeframe)
        candles = pd.DataFrame()
        candles["open"] = df["close"].resample(resample_str).first()
        candles["high"] = df["close"].resample(resample_str).max()
        candles["low"] = df["close"].resample(resample_str).min()
        candles["close"] = df["close"].resample(resample_str).last()
        candles["volume"] = df["volume"].resample(resample_str).sum()
        candles.dropna(inplace=True)
    else:
        if timeframe != "1s":
            resample_str = TIMEFRAME_MAP.get(timeframe)
            candles = df.resample(resample_str).agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).dropna()
        else:
            candles = df[["open", "high", "low", "close", "volume"]]

    return candles
