import pandas as pd
import numpy as np

def detect_manipulation(df: pd.DataFrame, range_info: dict) -> dict:
    """
    Detects the single most extreme manipulation event over the last 300 candles.
    A manipulation event involves price breaking out of a defined range and then returning inside.
    The "most extreme" is the candle with the close price furthest from the breached range boundary.
    """
    if df is None or df.empty:
        return {
            "manipulated": False, "returned_to_range": False, "direction": None,
            "status": "clean", "message": "Input DataFrame is empty.",
            "timestamp": None, "price": None
        }

    df_proc = df.copy().tail(300)  # Analyze only the last 300 candles
    df_proc.columns = [str(col).lower() for col in df_proc.columns]

    if "close" not in df_proc.columns:
        return {
            "manipulated": False, "returned_to_range": False, "direction": None,
            "status": "error", "message": "DataFrame missing required 'close' column.",
            "timestamp": None, "price": None
        }

    if 'range_low' not in range_info or 'range_high' not in range_info or \
       pd.isna(range_info['range_low']) or pd.isna(range_info['range_high']):
        return {
            "manipulated": False, "returned_to_range": False, "direction": None,
            "status": "clean", "message": "Valid range_low and range_high not provided in range_info.",
            "timestamp": None, "price": None
        }

    range_low = range_info["range_low"]
    range_high = range_info["range_high"]

    overall_most_extreme_candle_details = None
    overall_max_deviation = 0.0

    in_breakout_sequence = False
    current_sequence_direction = None
    current_sequence_extreme_candle_timestamp = None
    current_sequence_extreme_candle_close = None
    current_sequence_max_deviation = 0.0

    for timestamp, candle_row in df_proc.iterrows():
        close_price = candle_row["close"]

        if not in_breakout_sequence:
            if close_price > range_high:
                in_breakout_sequence = True
                current_sequence_direction = "up"
                current_sequence_max_deviation = close_price - range_high
                current_sequence_extreme_candle_timestamp = timestamp
                current_sequence_extreme_candle_close = close_price
            elif close_price < range_low:
                in_breakout_sequence = True
                current_sequence_direction = "down"
                current_sequence_max_deviation = range_low - close_price
                current_sequence_extreme_candle_timestamp = timestamp
                current_sequence_extreme_candle_close = close_price
        else:
            if current_sequence_direction == "up":
                if close_price > range_high:
                    deviation = close_price - range_high
                    if deviation > current_sequence_max_deviation:
                        current_sequence_max_deviation = deviation
                        current_sequence_extreme_candle_timestamp = timestamp
                        current_sequence_extreme_candle_close = close_price
                elif close_price < range_low:
                    in_breakout_sequence = True
                    current_sequence_direction = "down"
                    current_sequence_max_deviation = range_low - close_price
                    current_sequence_extreme_candle_timestamp = timestamp
                    current_sequence_extreme_candle_close = close_price
                elif range_low <= close_price <= range_high:
                    if current_sequence_max_deviation > overall_max_deviation:
                        overall_max_deviation = current_sequence_max_deviation
                        overall_most_extreme_candle_details = {
                            "timestamp": current_sequence_extreme_candle_timestamp,
                            "price": current_sequence_extreme_candle_close,
                            "direction": "up"
                        }
                    in_breakout_sequence = False

            elif current_sequence_direction == "down":
                if close_price < range_low:
                    deviation = range_low - close_price
                    if deviation > current_sequence_max_deviation:
                        current_sequence_max_deviation = deviation
                        current_sequence_extreme_candle_timestamp = timestamp
                        current_sequence_extreme_candle_close = close_price
                elif close_price > range_high:
                    in_breakout_sequence = True
                    current_sequence_direction = "up"
                    current_sequence_max_deviation = close_price - range_high
                    current_sequence_extreme_candle_timestamp = timestamp
                    current_sequence_extreme_candle_close = close_price
                elif range_low <= close_price <= range_high:
                    if current_sequence_max_deviation > overall_max_deviation:
                        overall_max_deviation = current_sequence_max_deviation
                        overall_most_extreme_candle_details = {
                            "timestamp": current_sequence_extreme_candle_timestamp,
                            "price": current_sequence_extreme_candle_close,
                            "direction": "down"
                        }
                    in_breakout_sequence = False

    if overall_most_extreme_candle_details:
        return {
            "manipulated": True,
            "returned_to_range": True,
            "direction": overall_most_extreme_candle_details["direction"],
            "status": "manipulated",
            "message": f"🟨 Manipulation detected. Most extreme close ({overall_most_extreme_candle_details['price']:.2f}) occurred during a breakout {overall_most_extreme_candle_details['direction']}.",
            "timestamp": pd.to_datetime(overall_most_extreme_candle_details["timestamp"]),
            "price": overall_most_extreme_candle_details["price"]
        }

    return {
        "manipulated": False,
        "returned_to_range": False,
        "direction": None,
        "status": "clean",
        "message": "No manipulation (breakout and return with an extreme candle) detected in the last 300 candles.",
        "timestamp": None,
        "price": None
    }
