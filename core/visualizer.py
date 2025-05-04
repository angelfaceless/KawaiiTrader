import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_full_analysis(df, symbol, timeframe, support_levels, resistance_levels, trendlines, fib_data, range_data):
    df = df.copy().tail(300)
    df.index.name = "Date"

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.set_facecolor("#d8bfe6")  # lilac background

    # 🕯️ Candlesticks
    width = 0.6
    for i, (_, row) in enumerate(df.iterrows()):
        color = "white" if row["close"] >= row["open"] else "black"
        ax.plot([i, i], [row["low"], row["high"]], color="black", linewidth=1)
        ax.add_patch(plt.Rectangle(
            (i - width / 2, min(row["open"], row["close"])),
            width,
            abs(row["close"] - row["open"]),
            facecolor=color,
            edgecolor="black"
        ))

    x_vals = np.arange(len(df))

    # 🟩 Support levels (solid pastel green lines)
    for level in support_levels:
        ax.axhline(y=level, color="#77dd77", linestyle="-", linewidth=1.2)

    # ➖ Trendlines (light grey solid)
    for role, trend in trendlines.items():
        slope = trend["slope"]
        intercept = trend["intercept"]
        start_idx = trend["start_index"]

        x_vals = np.arange(len(df) + 10)
        x_shifted = x_vals - start_idx
        y_vals = slope * x_shifted + intercept

        ax.plot(x_vals, y_vals, color="lightgrey", linestyle="-", linewidth=1.5)

    # 🟪 IRZ Fib levels
    if fib_data:
        anchor_index = len(df) - 11
        future_index = len(df) + 10

        for level, color in zip(fib_data["irz_levels"], ["#fffacd", "#ffe4b5", "#fffacd"]):  # pastel yellow/orange
            ax.plot([anchor_index, future_index], [level, level], color=color, linestyle="-", linewidth=1.2)

        for level in fib_data["target_levels"]:
            ax.plot([anchor_index, future_index], [level, level], color="white", linestyle="-", linewidth=1.5)

        # ✅ 1.0 Fib level — dashed white
        if "full_levels" in fib_data and 1.0 in fib_data["full_levels"]:
            level_1_0 = fib_data["full_levels"][1.0]
            ax.plot([anchor_index, future_index], [level_1_0, level_1_0],
                    color="white", linestyle="--", linewidth=1.2)

        ax.plot([anchor_index, future_index], [fib_data["anchor"], fib_data["anchor"]],
                color="gray", linestyle="-", linewidth=1.2)

    # 🔲 Range box (more transparent)
    if range_data.get("is_range", False):
        box_start = max(0, len(df) - 40)
        box_end = len(df) - 1
        box_width = box_end - box_start

        range_low = range_data["range_low"]
        range_high = range_data["range_high"]

        rect = patches.Rectangle(
            (box_start, range_low),
            width=box_width,
            height=range_high - range_low,
            linewidth=0,
            facecolor="purple",
            alpha=0.08  # even more transparent
        )
        ax.add_patch(rect)

    # 🖼️ Chart styling
    ax.set_title(f"{symbol} Analysis ({timeframe})", fontsize=14)
    ax.set_xlim(-1, len(df) + 10)
    ax.set_xlabel("Candles")
    ax.set_ylabel("Price")
    ax.grid(True)
    ax.set_xticks([])

    # 💾 Save to Charts/
    os.makedirs("Charts", exist_ok=True)
    chart_path = os.path.join("Charts", f"chart_{symbol}_{timeframe}.png")
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()
    return chart_path
