import os
from databento import Historical
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
API_KEY = os.getenv("DATABENTO_API_KEY")
client = Historical(key=API_KEY)

start_time = datetime.now(timezone.utc) - timedelta(hours=1)
end_time = datetime.now(timezone.utc)

data = client.timeseries.get_range(
    dataset="GLBX.MDP3",
    symbols=["ES.c.0"],
    stype_in="continuous",  # ✅ MATCHES ES.c.0 format
    schema="trades",
    start=start_time,
    end=end_time,
)

df = data.to_df() if data else pd.DataFrame()

if df.empty:
    print("[WARN] No data returned.")
else:
    latest_ts = pd.to_datetime(df["ts_event"]).max()
    print("[INFO] Latest ts_event:", latest_ts)
