from datetime import datetime
from zoneinfo import ZoneInfo

def format_report_discord(report) -> str:
    retrace_str = "\n".join(
        f"• {rt.label}: {rt.level}" for rt in report.retracements
    ) if report.retracements else "No retracement zone"

    target_str = "\n".join(
        f"🎯 **{t.label}**: {t.level}" for t in report.targets
    ) if report.targets else "No targets"

    manipulation_str = "\n".join(
        f"{m.timestamp} — Broke **{m.direction}** at {m.price}"
        for m in report.manipulations
    ) if report.manipulations else "No manipulation detected"

    if report.current_price is not None and report.current_price_time:
        dt_utc = datetime.fromisoformat(report.current_price_time)
        dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))
        readable_time = dt_est.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        current_price_str = f"📌 **Current Price:** {report.current_price} on {readable_time}\n"
    else:
        current_price_str = ""

    return f"""
**{report.symbol} — {report.timeframe} Report**
{current_price_str}
**Bias:** {report.directional_bias}
**Range:** {report.range_low} - {report.range_high}

**Support Levels:**
{', '.join(str(s) for s in report.support_levels)}

**Resistance Levels:**
{', '.join(str(r) for r in report.resistance_levels)}

**Trendlines:**
{report.trendline_summary or 'No trendlines'}

**Manipulation:**
{manipulation_str}

**IRZ Retracement Zone:**
{retrace_str}

{report.irz_message or ''}

{target_str}
""".strip()
