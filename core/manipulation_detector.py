import pandas as pd

def detect_manipulation(df: pd.DataFrame, range_info: dict) -> dict:
    """
    Detects if price wicked above/below a range and returned inside it.
    Works with real-time or historical data. Tracks status:
    - 'manipulated': broke and returned ✅
    - 'awaiting_return': broke, still outside ⏳
    - 'clean': no breakout ⬜
    """

    range_low = range_info["range_low"]
    range_high = range_info["range_high"]
    window = range_info.get("window", 50)  # how many bars formed the range

    # Normalize index/columns
    df = df.reset_index()
    df.columns = df.columns.str.lower()

    # Only look at candles that came after the consolidation
    post_range_df = df.iloc[-(len(df) - window):]

    direction = None
    breakout_idx = None
    returned_to_range = False
    manipulated = False

    # Step 1: Did we break above or below?
    for i, row in post_range_df.iterrows():
        if row["high"] > range_high:
            direction = "up"
            breakout_idx = i
            break
        elif row["low"] < range_low:
            direction = "down"
            breakout_idx = i
            break

    # Step 2: After breakout, did we return?
    if direction and breakout_idx is not None:
        subsequent = post_range_df.loc[breakout_idx:]
        for _, row in subsequent.iterrows():
            if range_low <= row["close"] <= range_high:
                returned_to_range = True
                manipulated = True
                break

    # Final result
    if manipulated:
        status = "manipulated"
        msg = (
            f"🟨 Manipulation detected — price broke {direction} and returned into the range."
        )
    elif direction:
        status = "awaiting_return"
        msg = (
            f"🟧 Breakout detected {direction} but price has NOT returned into the range yet."
        )
    else:
        status = "clean"
        msg = "No manipulation detected."

    result = {
        "manipulated": manipulated,
        "returned_to_range": returned_to_range,
        "direction": direction,
        "status": status,
        "message": msg,
    }

    # ✅ Only add price + timestamp if there was a breakout
    if direction and breakout_idx is not None:
        breakout_row = post_range_df.loc[breakout_idx]
        result["price"] = breakout_row["high"] if direction == "up" else breakout_row["low"]

        if "timestamp" in breakout_row:
            result["timestamp"] = str(breakout_row["timestamp"])
        elif post_range_df.index.name == "timestamp":
            result["timestamp"] = str(breakout_row.name)
        else:
            result["timestamp"] = "unknown"

    return result
