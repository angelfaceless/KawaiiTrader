import os
from datetime import datetime, timedelta

import pandas as pd
from dotenv import load_dotenv
from databento import Historical

# Load environment variables
load_dotenv()

client = Historical(key=os.getenv("DATABENTO_API_KEY"))

SCHEMA = "ohlcv-1m"

TIMEFRAME_MAP = {
    "1min": "1min",
    "5min": "5min",
    "15min": "15min",
    "30min": "30min",
    "1h": "1H",
    "1d": "1D"
}


def fetch_ohlcv(symbol: str, timeframe: str = "1h", lookback_days: int = 2) -> pd.DataFrame:
    if timeframe not in TIMEFRAME_MAP:
        raise ValueError(f"Unsupported timeframe: {timeframe}")

    now = datetime.utcnow().replace(second=0, microsecond=0)
    if "min" in timeframe:
        interval = int(timeframe.replace("min", ""))
        end_time = now - timedelta(minutes=now.minute % interval)
    elif "h" in timeframe:
        end_time = now.replace(minute=0)
    else:
        end_time = now

    start_time = end_time - timedelta(days=lookback_days)

    print(f"[Data] Fetching {symbol} from {start_time} to {end_time} on {timeframe} timeframe...")

    try:
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema=SCHEMA,
            symbols=symbol,
            stype_in="continuous",
            start=start_time,
            end=end_time,
        )
        df = data.to_df()

        # Use index as timestamp if Databento returns no explicit ts/ts_event column
        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError(
                f"[Databento Fetch Error] No usable timestamp index found in response. Columns: {list(df.columns)}"
            )

        df = df.copy()
        df.index.name = "timestamp"

        df = df[["open", "high", "low", "close", "volume"]]
        df = df.resample(TIMEFRAME_MAP[timeframe]).agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()

        return df

    except Exception as e:
        raise RuntimeError(f"[Databento Fetch Error] {e}")
