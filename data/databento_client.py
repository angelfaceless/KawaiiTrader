import os
import pandas as pd
from datetime import datetime, timedelta
from databento import Historical
from dotenv import load_dotenv

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("DATABENTO_API_KEY")

# User timeframe to Pandas-compatible string
TIMEFRAME_MAP = {
    "1min": "1min",
    "5min": "5min",
    "15min": "15min",
    "1h": "1h",
    "1d": "1d"
}

def fetch_ohlcv(symbol: str, timeframe: str = "15min", lookback_days: int = 2) -> pd.DataFrame:
    """Fetch tick data and resample to OHLCV."""
    try:
        print(f"[Analyzer] Fetching data for {symbol} on {timeframe} timeframe")

        # Clamp to valid interval (10 min data lag expected)
        now = datetime.utcnow().replace(second=0, microsecond=0)
        minute_mod = now.minute % 15
        aligned_now = now - timedelta(minutes=minute_mod)
        end_time = aligned_now - timedelta(minutes=15)
        start_time = end_time - timedelta(days=lookback_days)

        print(f"[Data] Fetching {symbol} from {start_time} to {end_time} on {timeframe} timeframe...")

        client = Historical(key=API_KEY)

        # Fetch raw trades
        data = client.timeseries.get_range(
            dataset="GLBX.MDP3",
            schema="trades",
            symbols=symbol,
            stype_in="continuous",
            start=start_time,
            end=end_time,
        )

        df = data.to_df()
        if df.empty:
            raise ValueError(f"[Databento Fetch Error] No usable data returned for {symbol}")

        # Convert ts_event to datetime index
        if "ts_event" not in df.columns:
            raise ValueError(f"[Databento Fetch Error] 'ts_event' missing from response. Columns: {df.columns.tolist()}")

        df["timestamp"] = pd.to_datetime(df["ts_event"])
        df.set_index("timestamp", inplace=True)

        # Resample to candles
        candles = df["price"].resample(TIMEFRAME_MAP[timeframe]).ohlc()
        candles["volume"] = df["size"].resample(TIMEFRAME_MAP[timeframe]).sum()
        candles.dropna(inplace=True)

        return candles

    except Exception as e:
        raise RuntimeError(f"[Databento Fetch Error] {e}")
