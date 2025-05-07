# kawaiitrader/core/irz_fib.py

def calculate_irz_projection(range_low: float, range_high: float, manipulation_direction: str) -> dict:
    """
    Projects a non-standard fib retracement and target structure based on direction.

    Args:
        range_low (float): Bottom of the range (body-based).
        range_high (float): Top of the range (body-based).
        manipulation_direction (str): 'up' or 'down'

    Returns:
        dict with levels and formatted message.
    """
    levels = {
        "1": None,
        "0.786": None,
        "0.707": None,
        "0.618": None,
        "0.5": None,
        "0": None,
        "-0.236": None,
        "-0.618": None,
        "-1": None
    }

    if manipulation_direction == "up":
        anchor_0 = range_low
        anchor_1 = range_high
        direction = "projected downward"
    elif manipulation_direction == "down":
        anchor_0 = range_high
        anchor_1 = range_low
        direction = "projected upward"
    else:
        return {"message": "🟪 No manipulation, so no IRZ projected."}

    diff = anchor_1 - anchor_0

    for key in levels.keys():
        k = float(key)
        levels[key] = round(anchor_0 + (diff * k), 2)

    msg = [f"🟪 IRZ Levels ({direction}):"]
    msg.append(f"Retrace Zone → {levels['0.618']} / {levels['0.707']} / {levels['0.786']}")
    msg.append(f"Profit Targets → {levels['-0.236']} / {levels['-0.618']} / {levels['-1']}")

    return {
        "levels": levels,
        "message": "\n".join(msg)
    }
