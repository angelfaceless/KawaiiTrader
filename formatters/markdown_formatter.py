# core/markdown_formatter.py

def escape_telegram(text) -> str:
    """
    Escapes special characters for Telegram MarkdownV2.
    Accepts any input and safely converts it to string.
    """
    text = str(text)
    for ch in r"_*[]()~`>#+-=|{}.!":
        text = text.replace(ch, f"\\{ch}")
    return text

def format_report_markdown(report) -> str:
    esc = escape_telegram

    retrace_str = "\n".join(
        f"• `{esc(r.label)}`: {esc(r.level)}" for r in report.retracements
    ) if report.retracements else "No retracement zone"

    target_str = "\n".join(
        f"🎯 *{esc(t.label)}*: `{esc(t.level)}`" for t in report.targets
    ) if report.targets else "No targets"

    manipulation_str = "\n".join(
        f"{esc(m.timestamp)} — Broke *{esc(m.direction)}* at `{esc(m.price)}`"
        for m in report.manipulations
    ) if report.manipulations else "No manipulation detected"

    return f"""
*{esc(report.symbol)} — {esc(report.timeframe)} Report*

*Bias:* {esc(report.directional_bias)}
*Range:* `{esc(report.range_low)} - {esc(report.range_high)}`

*Support Levels:*
{', '.join(f'`{esc(s)}`' for s in report.support_levels)}

*Resistance Levels:*
{', '.join(f'`{esc(r)}`' for r in report.resistance_levels)}

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
