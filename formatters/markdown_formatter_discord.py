from datetime import datetime
from zoneinfo import ZoneInfo

def format_trendline_for_report(trendline_messages):
    if not trendline_messages:
        return "None detected"
    return "\n".join(trendline_messages)

def format_htf_context(report):
    lines = ["📊 **HTF Context**"]

    for lvl, meta in report.confidence.get("support", {}).items():
        if isinstance(meta, dict) and meta.get("level") != "weak":
            tfs = ", ".join(meta.get("matched_timeframes", []))
            lines.append(f"• {lvl} (Support) — {meta['level']} alignment with {tfs}")

    for lvl, meta in report.confidence.get("resistance", {}).items():
        if isinstance(meta, dict) and meta.get("level") != "weak":
            tfs = ", ".join(meta.get("matched_timeframes", []))
            lines.append(f"• {lvl} (Resistance) — {meta['level']} alignment with {tfs}")

    for role, meta in report.confidence.get("trendline", {}).items():
        if isinstance(meta, dict) and meta.get("level") != "weak":
            tfs = ", ".join(meta.get("matched_timeframes", []))
            lines.append(f"• {role.capitalize()} trendline — {meta['level']} alignment with {tfs}")

    return "\n".join(lines) if len(lines) > 1 else "📊 **HTF Context**\nNo HTF Context Detected"

def format_report_discord(report) -> str:
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

    support_levels = [f"{s}" for s in report.support_levels]
    resistance_levels = [f"{r}" for r in report.resistance_levels]

    def group_levels(levels, group_size=3):
        return [" • ".join(levels[i:i+group_size]) for i in range(0, len(levels), group_size)]

    support_groups = group_levels(support_levels)
    resistance_groups = group_levels(resistance_levels)

    trendline_content = "None detected"
    if hasattr(report, 'trendline_messages') and report.trendline_messages:
        trendline_content = format_trendline_for_report(report.trendline_messages)
    elif hasattr(report, 'trendline_summary') and report.trendline_summary:
        trendline_content = report.trendline_summary if report.trendline_summary != "No active trendlines" else "None detected"

    manipulation_str = "None detected"
    if hasattr(report, 'manipulations') and report.manipulations:
        manipulation_str = "\n".join(
            f"• {m.timestamp} — **{m.direction}** at {m.price}"
            for m in report.manipulations
        )

    irz_content = "None available"
    if hasattr(report, 'irz_message') and report.irz_message:
        irz_content = report.irz_message
    else:
        retrace_str = ""
        if hasattr(report, 'retracements') and report.retracements:
            retrace_str = "Retracement Zone:\n" + "\n".join(
                f"🟠 {rt.label}: {rt.level}" for rt in report.retracements
            )

        target_str = ""
        if hasattr(report, 'targets') and report.targets:
            target_str = "Profit Targets:\n" + "\n".join(
                f"🎯 {t.label}: {t.level}" for t in report.targets
            )

        irz_parts = []
        if retrace_str:
            irz_parts.append(retrace_str)
        if target_str:
            irz_parts.append(target_str)
        if irz_parts:
            irz_content = "🟪 IRZ Levels (projected):\n\n" + "\n\n".join(irz_parts)
            if hasattr(report, 'invalidation_point') and report.invalidation_point:
                irz_content += f"\n\n⚠️ Invalidation Point: {report.invalidation_point}"

    header = f"**{report.symbol}** • {report.timeframe} • {current_price_str}"
    timestamp = f"_{date_str} at {time_str}_" if time_str and date_str else ""
    bias_range = f"**Bias:** {report.directional_bias} • **Range:** {report.range_low}-{report.range_high}"

    report_text = "━━━━━━━━━━━━━ 🌸🌸🌸 ━━━━━━━━━━━━━\n\n"

    if getattr(report, "kawaii_buy", False):
        report_text += (
            "╭───────────────────────────────╮\n"
            "         💖 KAWAII BUY 💖        \n"
            "╰───────────────────────────────╯\n\n"
        )

    report_text += header + "\n"
    if timestamp:
        report_text += timestamp + "\n"
    report_text += bias_range + "\n\n"

    report_text += "🟢 **Support** \n" + "\n".join(support_groups) + "\n\n"
    report_text += "🔴 **Resistance** \n" + "\n".join(resistance_groups) + "\n\n"
    report_text += "**Trendlines** 📈\n" + trendline_content + "\n\n"
    report_text += format_htf_context(report) + "\n\n"
    report_text += "⚡️ **Manipulation** ⚡️\n" + manipulation_str + "\n\n"
    report_text += "**IRZ Levels** 🎯\n" + irz_content + "\n\n"

    if hasattr(report, 'chart_path') and report.chart_path:
        report_text += "🖼️"

    return report_text.strip()

def integrate_trendlines_with_report(trendline_results, report):
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
