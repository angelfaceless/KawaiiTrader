from core.report_types import Retracement, Target

def calculate_irz_projection(range_low, range_high, manipulation_direction):
    try:
        # Reverse the projection direction — project *against* the manipulation
        if manipulation_direction == "down":
            fib_start = range_high
            fib_end = range_low
            anchor = range_high
            projection_direction = "up"
        elif manipulation_direction == "up":
            fib_start = range_low
            fib_end = range_high
            anchor = range_low
            projection_direction = "down"
        else:
            return {
                "message": "🟪 No valid manipulation direction.",
                "irz_zone": None,
                "retracements": [],
                "targets": [],
                "target_levels": [],
                "irz_levels": [],
                "anchor": None,
                "projection_direction": None,
                "full_levels": {}
            }

        diff = fib_end - fib_start

        fib_levels = {
            0.618: fib_start + diff * 0.618,
            0.707: fib_start + diff * 0.707,
            0.786: fib_start + diff * 0.786,
            -0.236: fib_start + diff * -0.236,
            -0.618: fib_start + diff * -0.618,
            -1.0: fib_start + diff * -1.0,
            1.0: fib_start + diff * 1.0,  # ✅ added
        }

        retracement_values = [
            round(fib_levels[0.618], 2),
            round(fib_levels[0.707], 2),
            round(fib_levels[0.786], 2),
        ]

        target_values = [
            round(fib_levels[-0.236], 2),
            round(fib_levels[-0.618], 2),
            round(fib_levels[-1.0], 2),
        ]

        retracement_objs = [
            Retracement(label="0.618", level=round(fib_levels[0.618], 2)),
            Retracement(label="0.707", level=round(fib_levels[0.707], 2)),
            Retracement(label="0.786", level=round(fib_levels[0.786], 2)),
        ]

        target_objs = [
            Target(label="-0.236", level=round(fib_levels[-0.236], 2)),
            Target(label="-0.618", level=round(fib_levels[-0.618], 2)),
            Target(label="-1.0", level=round(fib_levels[-1.0], 2)),
        ]

        message = f"""🟪 IRZ Levels (projected {'upward' if projection_direction == 'up' else 'downward'}):
Retrace Zone → {retracement_values[0]} / {retracement_values[1]} / {retracement_values[2]}
Profit Targets → {target_values[0]} / {target_values[1]} / {target_values[2]}"""

        irz_zone = f"{retracement_values[2]}–{retracement_values[0]}"

        return {
            "message": message,
            "irz_zone": irz_zone,
            "retracements": retracement_objs,
            "targets": target_objs,
            "target_levels": target_values,
            "irz_levels": retracement_values,
            "anchor": anchor,
            "projection_direction": projection_direction,
            "full_levels": fib_levels  # ✅ added
        }

    except Exception as e:
        return {
            "message": f"🟪 IRZ projection failed: {e}",
            "irz_zone": None,
            "retracements": [],
            "targets": [],
            "target_levels": [],
            "irz_levels": [],
            "anchor": None,
            "projection_direction": None,
            "full_levels": {}
        }
