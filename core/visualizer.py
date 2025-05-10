import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates
import datetime

def plot_full_analysis(df, symbol, timeframe, support_levels, resistance_levels, trendlines, fib_data, range_data):
    df = df.copy().tail(300)
    
    est_time_available = False
    df_est_index = df.index

    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception as e:
            print(f"Warning: Could not convert index to DatetimeIndex: {e}")

    if isinstance(df.index, pd.DatetimeIndex):
        try:
            if df.index.tz is None:
                df_est_index = df.index.tz_localize("UTC").tz_convert("US/Eastern")
            else:
                df_est_index = df.index.tz_convert("US/Eastern")
            est_time_available = True
        except Exception as e:
            print(f"Warning: Could not convert timestamps to EST: {e}")
            df_est_index = df.index
            est_time_available = False
    else:
        est_time_available = False

    fig, ax = plt.subplots(figsize=(20, 10))
    ax.set_facecolor("#d8bfe6")

    width = 0.6
    for i, (_, row) in enumerate(df.iterrows()):
        color = "white" if row["close"] >= row["open"] else "black"
        ax.plot([i, i], [row["low"], row["high"]], color="black", linewidth=1, zorder=1)
        body_patch = plt.Rectangle(
            (i - width / 2, min(row["open"], row["close"])),
            width,
            abs(row["close"] - row["open"]),
            facecolor=color,
            edgecolor="black",
            zorder=2
        )
        ax.add_patch(body_patch)

    for level in support_levels:
        ax.axhline(y=level, color="#77dd77", linestyle="-", linewidth=1.2, xmin=0, xmax=1, zorder=2.1)

    for role, trend in trendlines.items():
        slope = trend["slope"]
        intercept = trend["intercept"]
        start_idx = trend["start_index"]
        plot_x_vals = np.arange(len(df) + 10)
        x_shifted = plot_x_vals - start_idx
        y_vals = slope * x_shifted + intercept
        ax.plot(plot_x_vals, y_vals, color="lightgrey", linestyle="-", linewidth=1.5, zorder=2.2)

    if fib_data:
        anchor_index = len(df) - 11
        future_index = len(df) + 10
        for level, color_val in zip(fib_data.get("irz_levels", []), ["#fffacd", "#ffe4b5", "#fffacd"]):
            ax.plot([anchor_index, future_index], [level, level], color=color_val, linestyle="-", linewidth=1.2, zorder=2.3)
        for level in fib_data.get("target_levels", []):
            ax.plot([anchor_index, future_index], [level, level], color="white", linestyle="-", linewidth=1.5, zorder=2.3)
        if "full_levels" in fib_data and 1.0 in fib_data.get("full_levels", {}):
            level_1_0 = fib_data["full_levels"][1.0]
            ax.plot([anchor_index, future_index], [level_1_0, level_1_0],
                    color="white", linestyle="--", linewidth=1.2, zorder=2.3)
        if "anchor" in fib_data:
            ax.plot([anchor_index, future_index], [fib_data["anchor"], fib_data["anchor"]],
                    color="gray", linestyle="-", linewidth=1.2, zorder=2.3)

    if range_data.get("is_range", False):
        range_low = range_data["range_low"]
        range_high = range_data["range_high"]
        box_start_x = -0.5
        box_width_x = len(df)
        rect = patches.Rectangle(
            (box_start_x, range_low),
            width=box_width_x,
            height=range_high - range_low,
            linewidth=0,
            facecolor="purple",
            alpha=0.08,
            zorder=0
        )
        ax.add_patch(rect)
        mid_line_val = (range_low + range_high) / 2
        ax.plot([box_start_x, box_start_x + box_width_x], [mid_line_val, mid_line_val], color="white", linestyle="-", linewidth=1, zorder=0.5)

    ax.set_title(f"{symbol} Analysis ({timeframe})", fontsize=16)
    ax.set_xlim(-0.5, len(df) - 0.5 + 10)
    ax.set_ylabel("Price", fontsize=12)
    ax.grid(True, zorder=-1, linestyle=":", alpha=0.7)

    x_axis_label_text = "Time (EST)"

    if est_time_available and isinstance(df_est_index, pd.DatetimeIndex):
        if timeframe in ["1min", "5min", "15min", "1h"]:
            if timeframe == "1h":
                special_times_est = [
                    datetime.time(9, 0),
                    datetime.time(13, 0),
                    datetime.time(15, 0)
                ]
            else:
                special_times_est = [
                    datetime.time(9, 30),
                    datetime.time(10, 30),
                    datetime.time(12, 0),
                    datetime.time(13, 30),
                    datetime.time(15, 30)
                ]
            tick_positions = []
            tick_labels = []
            for i, ts_est in enumerate(df_est_index):
                if ts_est.time() in special_times_est:
                    tick_positions.append(i)
                    tick_labels.append(ts_est.strftime("%H:%M"))
            if tick_positions:
                ax.set_xticks(tick_positions)
                ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=10)
                ax.set_xlabel(x_axis_label_text, fontsize=12)
            else:
                ax.set_xticks([])
                ax.set_xlabel("Candles", fontsize=12)
        else:
            ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=7, integer=True))

            def format_fn(tick_val, tick_pos):
                if int(tick_val) >= 0 and int(tick_val) < len(df_est_index):
                    dt_obj = df_est_index[int(tick_val)]
                    if timeframe == "4h":
                        return dt_obj.strftime("%H:%M")
                    elif timeframe == "1d":
                        return dt_obj.strftime("%m-%d")
                    elif timeframe == "1w":
                        return dt_obj.strftime("%m-%d-%y")
                    elif timeframe == "1month":
                        return dt_obj.strftime("%m %y")
                return ""

            ax.xaxis.set_major_formatter(plt.FuncFormatter(format_fn))
            plt.xticks(rotation=45, ha="right", fontsize=10)
            if timeframe in ["1d", "1w", "1month"]:
                x_axis_label_text = "Date (EST)"
            ax.set_xlabel(x_axis_label_text, fontsize=12)
    else:
        ax.set_xticks([])
        ax.set_xlabel("Candles", fontsize=12)

    os.makedirs("Charts", exist_ok=True)
    chart_filename = f"chart_{symbol}_{timeframe}.jpg"
    chart_path = os.path.join("Charts", chart_filename)
    plt.tight_layout(pad=1.5)
    plt.savefig(chart_path, format="jpg", dpi=200, pil_kwargs={"quality": 95})
    plt.close(fig)
    return chart_path
