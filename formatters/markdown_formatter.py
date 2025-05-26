from datetime import datetime
from zoneinfo import ZoneInfo  # Requires Python 3.9+

def escape_telegram(text) -> str:
    """Escape special characters for Telegram markdown formatting"""
    text = str(text)
    for ch in r"_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text

def format_trendline_for_report(trendline_messages):
    """
    Format trendline messages in a sleek design while preserving all position states
    
    This function handles all position states including:
    - above (🔺)
    - below (🔻)
    - at (🟰)
    - touching (✋)
    """
    if not trendline_messages:
        return "None detected"
    
    formatted_messages = []
    for message in trendline_messages:
        # Split the message into lines
        lines = message.split('\n')
        # Extract the header (first line)
        header = lines[0]
        # Get the color emoji and trendline type
        parts = header.split(' ', 1)
        color_emoji = parts[0]
        trendline_type = parts[1] if len(parts) > 1 else ""
        
        # Process the bullet points to extract key information
        position_full = ""
        distance = ""
        touch_points = ""
        
        for line in lines[1:]:
            if "Position:" in line:
                position_full = line.split("Position:")[1].strip()
            elif "Distance:" in line:
                distance = line.split("Distance:")[1].strip()
            elif "Touch points:" in line:
                touch_points = line.split("Touch points:")[1].strip()
        
        # Create a more compact, sleek format that preserves all position states
        # Make sure to escape any hyphens in the distance value
        distance_escaped = escape_telegram(distance)
        formatted_message = f"{color_emoji} *{trendline_type}* • {position_full} • {distance_escaped}"
        formatted_messages.append(formatted_message)
    
    return "\n".join(formatted_messages)

def format_report_markdown(report, escape=True) -> str:
    """Format a complete analysis report for Telegram with a sleek, modern design"""

    def esc(text):
        return escape_telegram(text) if escape else str(text)

    # Format current price with timestamp
    if report.current_price is not None and report.current_price_time:
        dt_utc = datetime.fromisoformat(report.current_price_time)
        dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))
        time_str = dt_est.strftime("%I:%M %p %Z")
        date_str = dt_est.strftime("%b %d, %Y")
        current_price_str = f"{esc(report.current_price)}"
    else:
        time_str = ""
        date_str = ""
        current_price_str = "N/A"

    # Format support/resistance levels more compactly
    support_levels = [f"{esc(str(s))}" for s in report.support_levels]
    resistance_levels = [f"{esc(str(r))}" for r in report.resistance_levels]
    
    def group_levels(levels, group_size=3):
        result = []
        for i in range(0, len(levels), group_size):
            group = levels[i:i+group_size]
            result.append(" • ".join(group))
        return result
    
    support_groups = group_levels(support_levels)
    resistance_groups = group_levels(resistance_levels)

    # Format trendlines
    trendline_content = "None detected"
    if hasattr(report, 'trendline_messages') and report.trendline_messages:
        trendline_content = format_trendline_for_report(report.trendline_messages)
    elif hasattr(report, 'trendline_summary') and report.trendline_summary:
        if report.trendline_summary == "No active trendlines":
            trendline_content = "None detected"
        else:
            trendline_content = esc(report.trendline_summary)

    # Manipulation
    if hasattr(report, 'manipulations') and report.manipulations:
        manipulation_str = "\n".join(
            f"• {esc(m.timestamp)} — *{esc(m.direction)}* at {esc(m.price)}"
            for m in report.manipulations
        )
    else:
        manipulation_str = "None detected"

    # IRZ
    irz_content = "None available"
    if hasattr(report, 'irz_message') and report.irz_message:
        irz_content = esc(report.irz_message)

    # Header
    header = f"*{esc(report.symbol)}* • {esc(report.timeframe)} • {current_price_str}"
    timestamp = f"_{esc(date_str)} at {esc(time_str)}_" if time_str and date_str else ""
    range_text = f"{esc(report.range_low)}\\-{esc(report.range_high)}" if escape else f"{report.range_low}-{report.range_high}"
    bias_range = f"*Bias:* {esc(report.directional_bias)} • *Range:* {range_text}"

    # Final assembly
    report_text = header + "\n"
    if timestamp:
        report_text += timestamp + "\n"
    report_text += bias_range + "\n\n"
    
    report_text += "🟢 *Support* \n" + "\n".join(support_groups) + "\n\n"
    report_text += "🔴 *Resistance* \n" + "\n".join(resistance_groups) + "\n\n"
    report_text += "*Trendlines* 📈\n" + trendline_content + "\n\n"
    report_text += "⚡️ *Manipulation* ⚡️\n" + manipulation_str + "\n\n"
    report_text += "*IRZ Levels* 🎯\n" + irz_content + "\n\n"
    report_text += f"[🖼️]({esc(report.chart_path)})"

    return report_text.strip()

def integrate_trendlines_with_report(trendline_results, report):
    """
    Integrate trendline detection results with the report object
    """
    if trendline_results and isinstance(trendline_results, dict):
        messages = trendline_results.get("messages", [])
        if messages and isinstance(messages, list):
            report.trendline_messages = messages
            report.trendline_summary = "\n".join(messages)
        else:
            report.trendline_messages = []
            report.trendline_summary = "No active trendlines"

        vectors = trendline_results.get("vectors", {})
        if vectors and isinstance(vectors, dict):
            report.trendline_vectors = vectors
    else:
        report.trendline_messages = []
        report.trendline_summary = "No active trendlines"
        report.trendline_vectors = {}

    return report
