from datetime import datetime
from zoneinfo import ZoneInfo  # Requires Python 3.9+

def escape_telegram(text) -> str:
    text = str(text)
    for ch in r"_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text

def format_report_markdown(report) -> str:
    esc = escape_telegram

    # 🧠 Manipulation
    manipulation_str = "\n".join(
        f"{esc(m.timestamp)} — Broke *{esc(m.direction)}* at `{esc(m.price)}`"
        for m in report.manipulations
    ) if report.manipulations else "No manipulation detected"

    # 📌 Current Price
    if report.current_price is not None and report.current_price_time:
        dt_utc = datetime.fromisoformat(report.current_price_time)
        dt_est = dt_utc.astimezone(ZoneInfo("America/New_York"))
        readable_time = dt_est.strftime("%A, %B %d, %Y at %I:%M %p %Z")
        current_price_str = f"\n📌 *Current Price:* `{esc(report.current_price)}` on {esc(readable_time)}\n"
    else:
        current_price_str = ""

    # 🧱 Support/Resistance
    support_str = ", ".join(f"`{esc(str(s))}`" for s in report.support_levels)
    resistance_str = ", ".join(f"`{esc(str(r))}`" for r in report.resistance_levels)

    # 📉 IRZ + Targets
    irz_msg = f"\n\n*IRZ Levels:*\n{esc(report.irz_message)}" if report.irz_message else ""

    return f"""
*{esc(report.symbol)} — {esc(report.timeframe)} Report*{current_price_str}
*Bias:* {esc(report.directional_bias)}
*Range:* `{esc(report.range_low)} - {esc(report.range_high)}`

*Support Levels:*
{support_str}

*Resistance Levels:*
{resistance_str}

*Trendlines:*
{esc(report.trendline_summary or 'No trendlines')}

*Manipulation:*
{manipulation_str}{irz_msg}

🖼 [Chart Image]({esc(report.chart_path)})
""".strip()
