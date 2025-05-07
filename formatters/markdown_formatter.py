from datetime import datetime
from zoneinfo import ZoneInfo  # Requires Python 3.9+

def escape_telegram(text) -> str:
    text = str(text)
    for ch in r"_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text

def format_report_markdown(report) -> str:
    esc = escape_telegram

    retrace_str = "\n".join(
        f"• `{esc(rt.label)}`: {esc(rt.level)}" for rt in report.retracements
    ) if report.retracements else "No retracement zone"

    target_str = "\n".join(
        f"🎯 *{esc(t.label)}*: `{esc(t.level)}`" for t in report.targets
    ) if report.targets else "No targets"

    manipulation_str = "\n".join(
        f"{esc(m.timestamp)} — Broke *{esc(m.direction)}* at `{esc(m.price)}`"
        for m in report.manipulations
    ) if report.manipulations else "No manipulation detected"

    # ✅ Format current price and convert to America/New_York
    if report.current_price is not None and report.current_price_time:
        dt_utc = datetime.fromisoformat(report.current_price_time)
        dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))
        readable_time = dt_est.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        current_price_str = f"📌 *Current Price:* `{esc(report.current_price)}` on {esc(readable_time)}\n"
    else:
        current_price_str = ""

    return f"""
*{esc(report.symbol)} — {esc(report.timeframe)} Report*
{current_price_str}
*Bias:* {esc(report.directional_bias)}
*Range:* `{esc(report.range_low)} - {esc(report.range_high)}`

*Support Levels:*
{', '.join(f'`{esc(str(s))}`' for s in report.support_levels)}

*Resistance Levels:*
{', '.join(f'`{esc(str(r))}`' for r in report.resistance_levels)}

*Trendlines:*
{esc(report.trendline_summary or 'No trendlines')}

*Manipulation:*
{manipulation_str}

*IRZ Retracement Zone:*
{retrace_str}

{esc(report.irz_message or '')}

{target_str}

🖼 [Chart Image]({esc(report.chart_path)})
""".strip()
