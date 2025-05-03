def calculate_irz_projection(range_low, range_high, manipulation_direction):
    try:
        # Reverse the projection direction — project *against* the manipulation
        if manipulation_direction == "down":
            # Price broke down and came back = bullish reversal = project upward
            fib_start = range_high
            fib_end = range_low
            anchor = range_high
        elif manipulation_direction == "up":
            # Price broke up and came back = bearish reversal = project downward
            fib_start = range_low
            fib_end = range_high
            anchor = range_low
        else:
            return {
                "message": "🟪 No valid manipulation direction.",
                "irz_levels": [],
                "target_levels": [],
                "anchor": None
            }

        diff = fib_end - fib_start

        fib_levels = {
            0.618: fib_start + diff * 0.618,
            0.707: fib_start + diff * 0.707,
            0.786: fib_start + diff * 0.786,
            -0.236: fib_start + diff * -0.236,
            -0.618: fib_start + diff * -0.618,
            -1.0: fib_start + diff * -1.0,
        }

        irz_levels = [
            round(fib_levels[0.618], 2),
            round(fib_levels[0.707], 2),
            round(fib_levels[0.786], 2),
        ]

        target_levels = [
            round(fib_levels[-0.236], 2),
            round(fib_levels[-0.618], 2),
            round(fib_levels[-1.0], 2),
        ]

        message = f"""🟪 IRZ Levels (projected {'upward' if manipulation_direction == 'down' else 'downward'}):
Retrace Zone → {irz_levels[0]} / {irz_levels[1]} / {irz_levels[2]}
Profit Targets → {target_levels[0]} / {target_levels[1]} / {target_levels[2]}"""

        return {
            "message": message,
            "irz_levels": irz_levels,
            "target_levels": target_levels,
            "anchor": anchor
        }

    except Exception as e:
        return {
            "message": f"🟪 IRZ projection failed: {e}",
            "irz_levels": [],
            "target_levels": [],
            "anchor": None
        }
