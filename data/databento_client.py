# databento_client.py

import os
import math
import pandas as pd
from datetime import datetime, timedelta, timezone
from databento import Historical
from dotenv import load_dotenv

load_dotenv()

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
    """Calculate lookback days to cover at least target_candles for given timeframe."""
    seconds = TIMEFRAME_SECONDS.get(timeframe)
    if seconds is None:
        return 2  # default fallback
    return math.ceil((target_candles * seconds) / 86400)


def fetch_ohlcv(symbol: str, timeframe: str = "15min", lookback_days: int = None) -> pd.DataFrame:
    """Fetch OHLCV data using ohlcv_1s schema, falling back to raw trades if unsupported."""
    try:
        print(f"[Analyzer] Fetching data for {symbol} on {timeframe} timeframe")

        if lookback_days is None:
            lookback_days = get_dynamic_lookback(timeframe)

        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        minute_mod = now.minute % 15
        aligned_now = now - timedelta(minutes=minute_mod)
        end_time = aligned_now - timedelta(minutes=15)
        start_time = end_time - timedelta(days=lookback_days)

        print(f"[Data] Fetching {symbol} from {start_time} to {end_time} on {timeframe} timeframe...")

        # ✅ NEW: Load API key here to avoid issues with subprocesses
        api_key = os.getenv("DATABENTO_API_KEY")
        client = Historical(key=api_key)

        # Try ohlcv_1s first
        try:
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                schema="ohlcv_1s",
                symbols=symbol,
                stype_in="continuous",
                start=start_time,
                end=end_time,
            )
            df = data.to_df()
            required = {"open", "high", "low", "close", "volume", "ts_event"}
            if not required.issubset(df.columns):
                raise ValueError("Missing required OHLCV columns — falling back to trades")
        except Exception:
            print("[Fallback] Using raw trade data and resampling")
            data = client.timeseries.get_range(
                dataset="GLBX.MDP3",
                schema="trades",
                symbols=symbol,
                stype_in="continuous",
                start=start_time,
                end=end_time,
            )
            df = data.to_df()
            if "ts_event" not in df.columns or "price" not in df.columns or "size" not in df.columns:
                raise ValueError("Trades data missing required fields")

            df["timestamp"] = pd.to_datetime(df["ts_event"])
            df.set_index("timestamp", inplace=True)
            resample_str = TIMEFRAME_MAP.get(timeframe)
            if not resample_str:
                raise ValueError(f"Unsupported timeframe: {timeframe}")
            candles = df["price"].resample(resample_str).ohlc()
            candles["volume"] = df["size"].resample(resample_str).sum()
            candles.dropna(inplace=True)
            return candles

        # If ohlcv_1s worked
        df["timestamp"] = pd.to_datetime(df["ts_event"], unit="ns")
        df.set_index("timestamp", inplace=True)

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

    except Exception as e:
        raise RuntimeError(f"[Databento Fetch Error] {e}")
