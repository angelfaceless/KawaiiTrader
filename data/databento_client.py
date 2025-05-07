# data/databento_client.py

import os
import math
import pandas as pd
from datetime import datetime, timedelta, timezone
from databento import Historical
from dotenv import load_dotenv
import sys

load_dotenv()
API_KEY = os.getenv("DATABENTO_API_KEY")

TIMEFRAME_MAP = {
    "1min": "1T",
    "5min": "5T",
    "15min": "15T",
    "1h": "1H",
    "4h": "4H",
    "1d": "1D",
    "1w": "1W",
    "1month": "1M"
}

TIMEFRAME_SECONDS = {
    "1min": 60,
    "5min": 300,
    "15min": 900,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
    "1w": 604800,
    "1month": 2592000
}

def get_dynamic_lookback(timeframe: str, target_candles: int = None) -> int:
    if target_candles is not None:
        seconds = TIMEFRAME_SECONDS.get(timeframe)
        if seconds:
            return max(1, math.ceil((target_candles * seconds) / 86400))

    if timeframe in ["1min", "5min", "15min"]:
        return 2
    elif timeframe in ["1h", "4h"]:
        return 15
    elif timeframe == "1d":
        return 100
    elif timeframe == "1w":
        return 100
    elif timeframe == "1month":
        return 360
    return 7

def fetch_ohlcv(symbol_details: dict, timeframe: str, lookback_days: int = None) -> pd.DataFrame:
    if not API_KEY:
        raise ValueError("DATABENTO_API_KEY not found in environment or .env file.")

    client = Historical(key=API_KEY)

    db_symbol = symbol_details["db_symbol"]
    db_dataset = symbol_details["dataset"]
    db_stype_in = symbol_details["stype_in"]
    asset_class = symbol_details.get("asset_class", "unknown")

    end_time = datetime.now(timezone.utc).replace(second=0, microsecond=0) - timedelta(minutes=15)
    if lookback_days is None:
        lookback_days = get_dynamic_lookback(timeframe)
    start_time = end_time - timedelta(days=lookback_days)

    print(f"[Data] Fetching {db_symbol} from {db_dataset} ({db_stype_in}, {asset_class}) from {start_time} to {end_time} on {timeframe} timeframe...")
    sys.stdout.flush()

    df = pd.DataFrame()
    df_trades = pd.DataFrame()

    try:
        data = client.timeseries.get_range(
            dataset=db_dataset,
            symbols=[db_symbol],
            stype_in=db_stype_in,
            schema="ohlcv-1s",
            start=start_time,
            end=end_time,
        )
        df = data.to_df() if data else pd.DataFrame()

        if not df.empty:
            print(f"[DEBUG] OHLCV columns: {df.columns.tolist()}")
            print(f"[DEBUG] OHLCV preview:\n{df.head()}")
        else:
            print(f"[Warning] No OHLCV data — falling back to trades.")
            sys.stdout.flush()

            data_trades = client.timeseries.get_range(
                dataset=db_dataset,
                symbols=[db_symbol],
                stype_in=db_stype_in,
                schema="trades",
                start=start_time,
                end=end_time,
            )
            df_trades = data_trades.to_df() if data_trades else pd.DataFrame()

            if df_trades.empty:
                print(f"[Warning] Still no trade data.")
                return pd.DataFrame()

            if "ts_event" not in df_trades.columns:
                if "hd.ts_event" in df_trades.columns:
                    df_trades.rename(columns={"hd.ts_event": "ts_event"}, inplace=True)
                else:
                    raise KeyError("Missing ts_event or hd.ts_event in trades data.")

            df_trades["price"] = pd.to_numeric(df_trades["price"])
            df_trades["size"] = pd.to_numeric(df_trades["size"])
            df_trades.set_index(pd.to_datetime(df_trades["ts_event"]), inplace=True)

            rule = TIMEFRAME_MAP.get(timeframe)
            if not rule:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

            ohlc = df_trades["price"].resample(rule).ohlc()
            volume = df_trades["size"].resample(rule).sum()
            df = pd.concat([ohlc, volume], axis=1)
            df.rename(columns={"size": "volume"}, inplace=True)
            df.dropna(subset=["open", "high", "low", "close"], how="all", inplace=True)
            df["volume"] = df["volume"].fillna(0)

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("Expected OHLCV/trade data to have a DatetimeIndex.")

        if timeframe != "1s":
            rule = TIMEFRAME_MAP.get(timeframe)
            if not rule:
                raise ValueError(f"Unsupported timeframe for resampling: {timeframe}")

            df = df.resample(rule).agg({
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum"
            }).dropna(subset=["open", "high", "low", "close"], how="all")
            df["volume"] = df["volume"].fillna(0)

        if df.empty:
            print(f"[Warning] Final DataFrame is empty after processing for {db_symbol} on {timeframe}.")
        return df

    except Exception as e:
        print(f"[ERROR_HANDLER] Caught exception: {type(e).__name__} - {e}")
        sys.stdout.flush()
        error_message = str(e)

        if "data_end_after_available_end" in error_message.lower():
            try:
                actual_end_str_start = error_message.find("available up to ") + len("available up to ")
                actual_end_str_end = error_message.find(".", actual_end_str_start)
                if 0 <= actual_end_str_start < actual_end_str_end:
                    available_time = error_message[actual_end_str_start:actual_end_str_end]
                    print(f"[Data Hint] Databento says data ends at: {available_time}")
            except Exception as parse_e:
                print(f"[Debug] Failed to parse available end time: {parse_e}")
                sys.stdout.flush()

        err_sym_display = db_symbol or "unknown_symbol"
        if err_sym_display not in error_message and "Symbol:" not in error_message:
            error_message = f"Symbol: {err_sym_display} (Dataset: {db_dataset}) - {error_message}"

        raise RuntimeError(f"[Databento Fetch Error] {error_message}")
