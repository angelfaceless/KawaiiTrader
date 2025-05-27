import os
import math
import pandas as pd
from datetime import datetime, timedelta, timezone
import pytz
from databento import Historical
from dotenv import load_dotenv
import sys

load_dotenv()
API_KEY = os.getenv("DATABENTO_API_KEY")

TIMEFRAME_MAP = {
    "1min": "1min",
    "5min": "5min",
    "15min": "15min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1D",
    "1w": "1W",
    "1month": "1M",
    "1mo": "1M"
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

EST = pytz.timezone('US/Eastern')


def get_dynamic_lookback(timeframe: str, target_candles: int = None) -> int:
    if timeframe in ["5min", "15min"]:
        return 4
    if timeframe == "1min":
        return 3
    if timeframe in ["1h", "4h"]:
        return 15

    try:
        seconds = int(pd.to_timedelta(timeframe).total_seconds())
    except Exception:
        seconds = TIMEFRAME_SECONDS.get(timeframe, 60)

    if seconds >= 86400:
        return 365

    if 120 <= seconds < 300:
        return 4
    if 300 <= seconds <= 1800:
        return 4
    if 1860 <= seconds < 3600:
        return 15
    if 3600 < seconds <= 16200:
        return 100
    if 16201 <= seconds <= 97200:
        return 100

    if "mo" in timeframe:
        return 365

    if target_candles is not None:
        return max(1, math.ceil((target_candles * seconds) / 86400))

    return 7


def get_latest_available_end(symbol_details, timeframe) -> datetime:
    client = Historical(key=API_KEY)
    tf_sec = TIMEFRAME_SECONDS.get(timeframe, 60)
    now = datetime.now(timezone.utc)

    try:
        start = now - timedelta(minutes=5)
        data = client.timeseries.get_range(
            dataset=symbol_details["dataset"],
            symbols=[symbol_details["db_symbol"]],
            stype_in=symbol_details["stype_in"],
            schema="trades",
            start=start,
            end=now,
        )
        df = data.to_df() if data else pd.DataFrame()
        if df.empty:
            raise ValueError("No recent trades available.")
        if "ts_event" not in df.columns and "hd.ts_event" in df.columns:
            df.rename(columns={"hd.ts_event": "ts_event"}, inplace=True)
        latest_ts = pd.to_datetime(df["ts_event"]).max()
        aligned = latest_ts.floor(f"{tf_sec}s")
        print(f"[SYNC] Latest trade-aligned end time: {aligned}")
        return aligned
    except Exception as e:
        print(f"[WARN] Trade-based end time failed: {e}")
        return get_end_time_with_delay()


def get_end_time_with_delay(current_time=None):
    now_utc = datetime.now(timezone.utc)
    now_est = now_utc.astimezone(EST).replace(second=0, microsecond=0)

    if now_est.weekday() == 5:
        friday_est = now_est - timedelta(days=1)
        return friday_est.replace(hour=17, minute=0).astimezone(timezone.utc)
    elif now_est.weekday() == 6:
        if now_est.hour < 18:
            friday_est = now_est - timedelta(days=2)
            return friday_est.replace(hour=17, minute=0).astimezone(timezone.utc)
        else:
            return now_est.astimezone(timezone.utc)
    return now_est.astimezone(timezone.utc)


def fetch_ohlcv(symbol_details: dict, timeframe: str, lookback_days: int = None, current_time=None) -> pd.DataFrame:
    if not API_KEY:
        raise ValueError("DATABENTO_API_KEY not found.")

    client = Historical(key=API_KEY)
    db_symbol = symbol_details["db_symbol"]
    db_dataset = symbol_details["dataset"]
    db_stype_in = symbol_details["stype_in"]

    try:
        end_time = get_latest_available_end(symbol_details, timeframe)
    except Exception:
        print("[FALLBACK] Falling back to delayed end time.")
        end_time = get_end_time_with_delay()

    pad_seconds = TIMEFRAME_SECONDS.get(timeframe, 60)
    end_time_padded = end_time + timedelta(seconds=pad_seconds)

    if lookback_days is None:
        lookback_days = get_dynamic_lookback(timeframe)
    lookback_days = min(lookback_days, 365)
    start_time = end_time - timedelta(days=lookback_days)

    print(f"[DEBUG] {db_symbol} @ {timeframe} | Start: {start_time}, End: {end_time} (+pad) | Lookback: {lookback_days} days")
    sys.stdout.flush()

    df = pd.DataFrame()
    try:
        data = client.timeseries.get_range(
            dataset=db_dataset,
            symbols=[db_symbol],
            stype_in=db_stype_in,
            schema="ohlcv-1s",
            start=start_time,
            end=end_time_padded,
        )
        df = data.to_df() if data else pd.DataFrame()
    except Exception as e:
        msg = str(e)
        if "data_end_after_available_end" in msg and "available up to " in msg:
            corrected = msg.split("available up to ")[1].split(".")[0]
            safe_end_time = pd.to_datetime(corrected)
            print(f"[FALLBACK] Available end: {safe_end_time}")
            data = client.timeseries.get_range(
                dataset=db_dataset,
                symbols=[db_symbol],
                stype_in=db_stype_in,
                schema="ohlcv-1s",
                start=start_time,
                end=safe_end_time,
            )
            df = data.to_df() if data else pd.DataFrame()
            end_time = safe_end_time
        else:
            raise

    if df.empty:
        print(f"[Warning] No OHLCV data — falling back to trades.")
        data_trades = client.timeseries.get_range(
            dataset=db_dataset,
            symbols=[db_symbol],
            stype_in=db_stype_in,
            schema="trades",
            start=start_time,
            end=end_time_padded,
        )
        df_trades = data_trades.to_df() if data_trades else pd.DataFrame()
        if df_trades.empty:
            print(f"[Warning] Still no trade data.")
            return pd.DataFrame()
        if "ts_event" not in df_trades.columns and "hd.ts_event" in df_trades.columns:
            df_trades.rename(columns={"hd.ts_event": "ts_event"}, inplace=True)
        df_trades["price"] = pd.to_numeric(df_trades["price"])
        df_trades["size"] = pd.to_numeric(df_trades["size"])
        df_trades.set_index(pd.to_datetime(df_trades["ts_event"]), inplace=True)

        rule = TIMEFRAME_MAP.get(timeframe)
        if rule is None:
            try:
                rule = pd.to_timedelta(timeframe)
            except Exception:
                raise ValueError(f"Invalid timeframe: {timeframe}")

        ohlc = df_trades["price"].resample(rule).ohlc()
        volume = df_trades["size"].resample(rule).sum()
        df = pd.concat([ohlc, volume], axis=1)
        df.rename(columns={"size": "volume"}, inplace=True)
        df.dropna(subset=["open", "high", "low", "close"], how="all", inplace=True)
        df["volume"] = df["volume"].fillna(0)

    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError("Expected DatetimeIndex")

    if timeframe == "1mo":
        df = df.resample("1M").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna(subset=["open", "high", "low", "close"], how="all")
        df["volume"] = df["volume"].fillna(0)
    elif timeframe != "1s":
        rule = TIMEFRAME_MAP.get(timeframe)
        if rule is None:
            try:
                rule = pd.to_timedelta(timeframe)
            except Exception:
                raise ValueError(f"Invalid timeframe: {timeframe}")
        df = df.resample(rule).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna(subset=["open", "high", "low", "close"], how="all")
        df["volume"] = df["volume"].fillna(0)

    return df
