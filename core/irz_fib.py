def calculate_irz_projection(range_low, range_high, manipulation_direction, breakouts):
    """
    Custom IRZ and Fibonacci projection logic using fixed levels and manipulation direction.
    Projects Fibs in the direction opposite to the manipulation, anchored to the range body.

    Args:
        range_low (float): Lower bound of full-body range.
        range_high (float): Upper bound of full-body range.
        manipulation_direction (str): 'above' or 'below'.
        breakouts (list): List of breakout timestamps (used elsewhere if needed).

    Returns:
        dict: {
            'levels': dict of level -> projected price,
            'irz': [0.618, 0.707, 0.786],  # always same
            'targets': [0, -0.236, -0.618, -1],  # always same
            'direction': 'down' or 'up'
        }
    """

    fib_levels = [0, 0.618, 1, 0.707, 0.786, -0.236, 0.5, -0.618, -1]
    irz_levels = [0.618, 0.707, 0.786]
    target_levels = [0, -0.236, -0.618, -1]

    if manipulation_direction == 'above':
        anchor_0 = range_low
        anchor_1 = range_high
        direction = 'down'
    elif manipulation_direction == 'below':
        anchor_0 = range_high
        anchor_1 = range_low
        direction = 'up'
    else:
        raise ValueError("manipulation_direction must be 'above' or 'below'")

    delta = anchor_1 - anchor_0
    levels = {level: anchor_0 + delta * level for level in fib_levels}

    return {
        'levels': levels,
        'irz': irz_levels,
        'targets': target_levels,
        'direction': direction
    }
