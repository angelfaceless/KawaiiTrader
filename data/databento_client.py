import os
import math
import pandas as pd
from datetime import datetime, timedelta, timezone

MAX_DATA_DELAY = timedelta(minutes=15)
MAX_AVAILABLE_END = datetime(2025, 5, 3, 0, 0, 0, tzinfo=timezone.utc)

from databento import Historical
from dotenv import load_dotenv
from utils.symbols import resolve_symbol_alias

load_dotenv()
API_KEY = os.getenv("DATABENTO_API_KEY")

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
    return math.ceil((target_candles * seconds) / 86400) if seconds else 2


def is_weekend(dt: datetime) -> bool:
    return dt.weekday() in (5, 6)


def fetch_ohlcv(symbol: str, timeframe: str = "15min", lookback_days: int = None) -> pd.DataFrame:
    original_symbol = symbol

    try:
        symbol = resolve_symbol_alias(symbol)
        if symbol.endswith(".c.0"):
            symbol = symbol.split(".")[0]

        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        minute_mod = now.minute % 15
        aligned_now = now - timedelta(minutes=minute_mod)
        end_time = aligned_now - MAX_DATA_DELAY
        if end_time > MAX_AVAILABLE_END:
            end_time = MAX_AVAILABLE_END

        # ✅ Weekend lookback patch
        if is_weekend(now):
            print(f"[Resolver] Weekend detected — extending lookback to 3 days")
            lookback_days = 3

        start_time = end_time - timedelta(days=lookback_days or get_dynamic_lookback(timeframe))

        # ✅ Patch: BTC must use GLBX.MDP3
        if "BTC" in symbol or "/USD" in symbol:
            dataset = "GLBX.MDP3"
            stype = "raw_symbol"
        else:
            dataset = "GLBX.MDP3"
            if is_weekend(now):
                print(f"[Resolver] Weekend detected. Falling back to front-month for {symbol}")
                fallback_contracts = {
                    "ES": "ESM5",
                    "MES": "MESM5",
                    "NQ": "NQM5",
                    "MNQ": "MNQM5",
                    "RTY": "RTYM5",
                    "YM": "YMM5"
                }
                symbol = fallback_contracts.get(symbol, symbol)
                stype = "raw_symbol"
            else:
                stype = "parent"

        print(f"[Analyzer] Fetching data for {symbol} on {timeframe} timeframe")
        print(f"[Data] Fetching {symbol} from {start_time} to {end_time} on {timeframe} timeframe...")

        client = Historical(key=API_KEY)

        try:
            data = client.timeseries.get_range(
                dataset=dataset,
                schema="ohlcv_1s",
                symbols=symbol,
                stype_in=stype,
                start=start_time,
                end=end_time,
            )
            df = data.to_df()
            if df is None or df.empty or "ts_event" not in df.columns:
                raise ValueError("ohlcv_1s missing or invalid")
        except Exception as e:
            print(f"[Fallback] ohlcv_1s failed ({e}), retrying with raw trades")
            data = client.timeseries.get_range(
                dataset=dataset,
                schema="trades",
                symbols=symbol,
                stype_in=stype,
                start=start_time,
                end=end_time,
            )
            if not data:
                print("[ERROR] Databento returned no trade data.")
                return None
            df = data.to_df()
            if df is None or df.empty or "ts_event" not in df.columns:
                print("[ERROR] Trade data invalid or empty.")
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

    except Exception as e:
        print(f"[ERROR] Failed to analyze {original_symbol} on {timeframe}: {e}")
        return None
