import pandas as pd

def resample_trades_to_ohlcv(df_trades: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    rule = timeframe if timeframe != "1mo" else "1M"

    ohlc = df_trades["price"].resample(rule).ohlc()
    volume = df_trades["size"].resample(rule).sum()
    df = pd.concat([ohlc, volume], axis=1)
    df.rename(columns={"size": "volume"}, inplace=True)
    df.dropna(subset=["open", "high", "low", "close"], how="all", inplace=True)
    df["volume"] = df["volume"].fillna(0)
    return df
