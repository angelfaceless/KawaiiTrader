from datetime import datetime
from zoneinfo import ZoneInfo

def format_report_discord(report) -> str:
    """
    Format a complete analysis report for Discord matching the Telegram format
    
    This formatter produces output that exactly matches the Telegram format:
    - Symbol, timeframe, and price on first line
    - Date and time on second line
    - Bias and range on third line
    - Support and resistance with bullet points grouped in threes
    - Trendlines with original bullet point format
    - Manipulation and IRZ sections with proper formatting
    """
    # Format current price with timestamp
    if report.current_price is not None and report.current_price_time:
        dt_utc = datetime.fromisoformat(report.current_price_time)
        dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))
        time_str = dt_est.strftime("%I:%M %p %Z")
        date_str = dt_est.strftime("%b %d, %Y")
        current_price_str = f"{report.current_price}"
    else:
        time_str = ""
        date_str = ""
        current_price_str = "N/A"

    # Format support/resistance levels more compactly with bullet points
    support_levels = [f"{s}" for s in report.support_levels]
    resistance_levels = [f"{r}" for r in report.resistance_levels]
    
    # Group levels in threes for compact display
    def group_levels(levels, group_size=3):
        result = []
        for i in range(0, len(levels), group_size):
            group = levels[i:i+group_size]
            result.append(" • ".join(group))
        return result
    
    support_groups = group_levels(support_levels)
    resistance_groups = group_levels(resistance_levels)
    
    # Format trendlines - preserve the exact format from trendline_messages if available
    trendline_content = "None detected"
    if hasattr(report, 'trendline_messages') and report.trendline_messages:
        trendline_content = "\n".join(report.trendline_messages)
    elif hasattr(report, 'trendline_summary') and report.trendline_summary:
        if report.trendline_summary == "No active trendlines":
            trendline_content = "None detected"
        else:
            trendline_content = report.trendline_summary
    
    # Format manipulation data
    manipulation_str = "None detected"
    if hasattr(report, 'manipulations') and report.manipulations:
        manipulation_str = "\n".join(
            f"{m.timestamp} — {m.direction} at {m.price}"
            for m in report.manipulations
        )

    # Format IRZ data
    irz_content = ""
    
    # Format retracements if available
    retrace_str = ""
    if hasattr(report, 'retracements') and report.retracements:
        retrace_str = "Retracement Zone:\n" + "\n".join(
            f"🟠 {rt.label}: {rt.level}" for rt in report.retracements
        )
    
    # Format targets if available
    target_str = ""
    if hasattr(report, 'targets') and report.targets:
        target_str = "Profit Targets:\n" + "\n".join(
            f"🎯 {t.label}: {t.level}" for t in report.targets
        )
    
    # Use IRZ message if available
    if hasattr(report, 'irz_message') and report.irz_message:
        irz_content = report.irz_message
    else:
        # Otherwise build from components
        irz_parts = []
        if retrace_str:
            irz_parts.append(retrace_str)
        if target_str:
            irz_parts.append(target_str)
        if irz_parts:
            irz_content = "🟪 IRZ Levels (projected):\n\n" + "\n\n".join(irz_parts)
            if hasattr(report, 'invalidation_point') and report.invalidation_point:
                irz_content += f"\n\n⚠️ Invalidation Point: {report.invalidation_point}"
        else:
            irz_content = "None available"

    # Create header with symbol, timeframe, and price
    header = f"{report.symbol} • {report.timeframe} • {current_price_str}"
    
    # Create timestamp line
    timestamp = f"{date_str} at {time_str}" if time_str and date_str else ""
    
    # Create bias and range line
    bias_range = f"Bias: {report.directional_bias} • Range: {report.range_low}-{report.range_high}"

    # Build the report matching the Telegram format
    report_text = header + "\n"
    if timestamp:
        report_text += timestamp + "\n"
    report_text += bias_range + "\n\n"
    
    report_text += "🟢 Support \n"
    report_text += "\n".join(support_groups) + "\n\n"
    
    report_text += "🔴 Resistance \n"
    report_text += "\n".join(resistance_groups) + "\n\n"
    
    report_text += "Trendlines 📈\n"
    report_text += trendline_content + "\n\n"
    
    report_text += "⚡️Manipulation⚡️\n"
    report_text += manipulation_str + "\n\n"
    
    report_text += "IRZ Levels 🎯\n"
    report_text += irz_content + "\n\n"
    
    report_text += "🖼️"
    
    return report_text.strip()

# Example of how to integrate the trendline detector with the report formatter
def integrate_trendlines_with_report(trendline_results, report):
    """
    Integrate trendline detection results with the report object
    
    Parameters:
    - trendline_results: The result from detect_trendline function
    - report: The report object to update
    
    Returns:
    - Updated report object with trendline information
    """
    # More robust handling of trendline results
    if trendline_results and isinstance(trendline_results, dict):
        # Store the raw trendline messages for formatting
        messages = trendline_results.get("messages", [])
        if messages and isinstance(messages, list):
            report.trendline_messages = messages
            
            # Create a summary for backward compatibility
            report.trendline_summary = "\n".join(messages)
        else:
            report.trendline_messages = []
            report.trendline_summary = "No active trendlines"
        
        # Store vector information if needed for further analysis
        vectors = trendline_results.get("vectors", {})
        if vectors and isinstance(vectors, dict):
            report.trendline_vectors = vectors
    else:
        # Default values if trendline_results is None or invalid
        report.trendline_messages = []
        report.trendline_summary = "No active trendlines"
        report.trendline_vectors = {}
    
    return report
