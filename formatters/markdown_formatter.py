import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.report_types import Report

def format_report_markdown(report: Report) -> str:
    lines = []
    lines.append(f"🌸 *{report.symbol.upper()} Report @ {report.timeframe}*")
    lines.append(f"🔹 Range: `{report.range_low}` to `{report.range_high}`")
    lines.append(f"📈 Bias: *{report.directional_bias}*")

    if report.support_levels:
        levels = ", ".join([f"{lvl:.2f}" for lvl in report.support_levels])
        lines.append(f"\n🟦 *Support Levels:* {levels}")

    if report.resistance_levels:
        levels = ", ".join([f"{lvl:.2f}" for lvl in report.resistance_levels])
        lines.append(f"🟥 *Resistance Levels:* {levels}")

    if report.trendline_summary:
        lines.append(f"\n📐 *Trendline Summary:*\n{report.trendline_summary}")

    # 🟪 IRZ Section
    if report.irz_message or report.retracements or report.targets:
        if report.irz_message:
            direction_line = report.irz_message.split(":")[0].replace("🟪", "").strip()
            lines.append(f"\n🟪 *{direction_line}*")
        if report.irz_zone:
            lines.append(f"IRZ Zone: `{report.irz_zone}`")
        if report.retracements:
            lines.append("\n🔄 *Retracement Levels:*")
            for r in report.retracements:
                lines.append(f"• `{r.label}` → `{r.level:.2f}`")
        if report.targets:
            lines.append("\n🎯 *Targets:*")
            for t in report.targets:
                lines.append(f"• `{t.label}` → `{t.level:.2f}`")

    if report.manipulations:
        lines.append("\n⚠️ *Manipulation Events:*")
        for m in report.manipulations:
            lines.append(f"• `{m.direction}` at `{m.price:.2f}` ({m.timestamp})")

    if report.chart_path:
        lines.append(f"\n📈 Chart saved to: `{report.chart_path}`")

    return "\n".join(lines)
