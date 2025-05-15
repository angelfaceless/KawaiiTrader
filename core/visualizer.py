import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
# import matplotlib.dates as mdates # Not strictly needed for current date formatting
import datetime

def plot_full_analysis(df, symbol, timeframe, support_levels, resistance_levels, trendlines, fib_data, range_data):
    # df is the original, unsliced DataFrame from analyzer.py

    # Determine the slice of the DataFrame to display based on timeframe
    if timeframe == "1min":
        df_display = df.copy().tail(150)
        width = 0.7
        x_pad = 20
        y_zoom = True
    elif timeframe == "5min":
        df_display = df.copy().tail(200)
        width = 0.65
        x_pad = 10
        y_zoom = True
    elif timeframe == "15min":
        df_display = df.copy().tail(250)
        width = 0.6
        x_pad = 8
        y_zoom = True
    elif timeframe == "1h":
        df_display = df.copy().tail(250)
        width = 0.6
        x_pad = 5
        y_zoom = True
    elif timeframe == "1d":
        df_display = df.copy().tail(200)
        width = 0.7
        x_pad = 10
        y_zoom = True
    elif timeframe == "1w":
        df_display = df.copy().tail(150)
        width = 0.65
        x_pad = 6
        y_zoom = True
    elif timeframe == "4h" or timeframe == "1month": # Assuming 1month is a valid timeframe string
        df_display = df.copy().tail(300)
        width = 0.6
        x_pad = 5
        y_zoom = True
    else:
        df_display = df.copy().tail(300)
        width = 0.6
        x_pad = 5
        y_zoom = False

    est_time_available = False
    # Use the index from the sliced df_display for x-axis date formatting
    df_display_est_index = df_display.index 

    if not isinstance(df_display.index, pd.DatetimeIndex):
        try:
            # Create a new DataFrame for modification to avoid SettingWithCopyWarning on df_display
            df_display_copy = df_display.copy()
            df_display_copy.index = pd.to_datetime(df_display_copy.index)
            df_display = df_display_copy # Assign back if conversion is successful
            df_display_est_index = df_display.index
        except Exception as e:
            print(f"Warning: Could not convert display index to DatetimeIndex: {e}")

    if isinstance(df_display.index, pd.DatetimeIndex):
        try:
            if df_display.index.tz is None:
                df_display_est_index = df_display.index.tz_localize("UTC").tz_convert("US/Eastern")
            else:
                df_display_est_index = df_display.index.tz_convert("US/Eastern")
            est_time_available = True
        except Exception as e:
            print(f"Warning: Could not convert display timestamps to EST: {e}")
            df_display_est_index = df_display.index # Fallback to original display index
            est_time_available = False
    else:
        est_time_available = False

    fig_width = max(20, len(df_display) * 0.08)
    fig_height = 10
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_facecolor("#d8bfe6")

    # Plot candles using 0-based indexing for the df_display
    for i, (_, row) in enumerate(df_display.iterrows()):
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
        ax.axhline(y=level, color="#77dd77", linestyle="-", linewidth=1.2, zorder=2.1)

    # Corrected Trendline Plotting
    # The 'df' argument is the original, full DataFrame passed from analyzer.py
    original_index_offset_of_display_slice = len(df) - len(df_display)

    for role, trend in trendlines.items():
        slope = trend["slope"]
        intercept = trend["intercept"]

        # x-coordinates on the current display plot (0 to len(df_display)-1, extended)
        x_coords_on_display_plot = np.arange(0, len(df_display) + 10) 

        # Map these display plot x-coordinates to their corresponding original df integer indices
        original_indices_for_trend_calc = original_index_offset_of_display_slice + x_coords_on_display_plot
        
        # Calculate y-values using the trendline's slope and intercept with original indices
        y_values_for_trend_on_display_plot = slope * original_indices_for_trend_calc + intercept
        
        # Increased linewidth for prominence, color kept as white
        ax.plot(x_coords_on_display_plot, y_values_for_trend_on_display_plot, color="white", linestyle="-", linewidth=2.0, zorder=2.2)

    if fib_data:
        # Anchor fib lines relative to the end of the displayed data
        anchor_plot_index = len(df_display) - 11 
        future_plot_index = len(df_display) + 10
        for level, color_val in zip(fib_data.get("irz_levels", []), ["#fffacd", "#ffe4b5", "#fffacd"]):
            ax.plot([anchor_plot_index, future_plot_index], [level, level], color=color_val, linestyle="-", linewidth=1.2, zorder=2.3)
        for level in fib_data.get("target_levels", []):
            ax.plot([anchor_plot_index, future_plot_index], [level, level], color="white", linestyle="-", linewidth=1.5, zorder=2.3)
        if "full_levels" in fib_data and 1.0 in fib_data.get("full_levels", {}):
            ax.plot([anchor_plot_index, future_plot_index], [fib_data["full_levels"][1.0]]*2,
                    color="white", linestyle="--", linewidth=1.2, zorder=2.3)
        if "anchor" in fib_data:
            ax.plot([anchor_plot_index, future_plot_index], [fib_data["anchor"]]*2,
                    color="gray", linestyle="-", linewidth=1.2, zorder=2.3)

    if range_data.get("is_range", False):
        range_low = range_data["range_low"]
        range_high = range_data["range_high"]
        rect = patches.Rectangle(
            (-0.5, range_low),
            width=len(df_display), # Width should be for the displayed part
            height=range_high - range_low,
            linewidth=0,
            facecolor="purple",
            alpha=0.08,
            zorder=0
        )
        ax.add_patch(rect)
        ax.plot([-0.5, len(df_display)], [(range_low + range_high)/2]*2, color="white", linewidth=1, zorder=0.5)

    fib_right_pad = 10 if fib_data else 0
    ax.set_xlim(-x_pad, len(df_display) - 1 + x_pad + fib_right_pad)

    if y_zoom:
        price_bounds = [df_display["low"].min(), df_display["high"].max()]
        if fib_data:
            price_bounds += fib_data.get("target_levels", []) + fib_data.get("irz_levels", [])
            if "full_levels" in fib_data:
                price_bounds += list(fib_data["full_levels"].values())
            if "anchor" in fib_data:
                price_bounds.append(fib_data["anchor"])
        low, high = min(price_bounds), max(price_bounds)
        margin_factor = (
            0.005 if timeframe == "1min" else
            0.003 if timeframe == "5min" else
            0.0015 if timeframe == "15min" else
            0.0012 if timeframe == "1h" else
            0.001
        )
        margin = (high - low) * margin_factor
        ax.set_ylim(low - margin, high + margin)

    ax.set_title(f"{symbol} Analysis ({timeframe})", fontsize=16)
    ax.set_ylabel("Price", fontsize=12)
    ax.grid(True, zorder=-1, linestyle=":", alpha=0.7)

    if est_time_available:
        if timeframe in ["1min", "5min", "15min", "1h"]:
            special_times = [datetime.time(9,30), datetime.time(10,30), datetime.time(13,30), datetime.time(15,30)]
            tick_pos = [i for i, ts in enumerate(df_display_est_index) if isinstance(ts, datetime.datetime) and ts.time() in special_times]
            tick_labels = [df_display_est_index[i].strftime("%H:%M") for i in tick_pos if i < len(df_display_est_index)]
            ax.set_xticks(tick_pos)
            ax.set_xticklabels(tick_labels, rotation=45, ha="right", fontsize=10)
        else:
            ax.xaxis.set_major_locator(plt.MaxNLocator(nbins=7, integer=True))
            ax.xaxis.set_major_formatter(plt.FuncFormatter(
                lambda x, _: df_display_est_index[int(x)].strftime("%m-%d") if 0 <= int(x) < len(df_display_est_index) and isinstance(df_display_est_index[int(x)], datetime.datetime) else ""
            ))
            plt.xticks(rotation=45, ha="right", fontsize=10)
        ax.set_xlabel("Time (EST)", fontsize=12)
    else:
        ax.set_xticks([]) 
        ax.set_xlabel("Candles", fontsize=12)

    os.makedirs("Charts", exist_ok=True)
    chart_path = os.path.join("Charts", f"chart_{symbol}_{timeframe}.png")
    plt.tight_layout(pad=1.0)
    plt.savefig(chart_path, format="png", dpi=300)
    plt.close(fig)
    return chart_path

