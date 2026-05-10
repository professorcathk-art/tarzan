"""Minimal inline-CSS templates for transactional email."""

from __future__ import annotations



def render_schedule_email(template_name: str, summary_lines: list[str], rows: list[dict]) -> tuple[str, str]:



    body_rows = "".join(
        f"<tr style='border-bottom:1px solid #eaeaea;'>"
        f"<td style='padding:8px;'>{idx+1}</td>"
        f"<td style='padding:8px;font-weight:600;'>{r.get('ticker','')}</td>"
        f"<td style='padding:8px;'>{str(r.get('reason',''))[:220]}</td>"
        f"</tr>"
        for idx, r in enumerate(rows[:50])


    )


    summary_html = "".join(
        f"<p style='margin:4px 0;font-family:Arial,sans-serif;color:#444;'>{line}</p>" for line in summary_lines
    )


    disclaimer = (
        "<p style='font-size:12px;color:#777;font-family:Arial,sans-serif;line-height:1.4;'>"

        "過去回測與篩選結果不構成投資建議。資訊僅供研究參考，請自行評估風險。"

        "</p>"


    )



    html = (
        "<html><body style='background:#fafafa;margin:0;padding:24px;'>"
        "<div style='max-width:720px;margin:0 auto;background:#fff;border-radius:10px;border:1px solid #eaeaea;padding:22px;'>"
        f"<h1 style='font-family:Arial,sans-serif;font-size:20px;margin-bottom:16px;color:#111;'>{template_name}</h1>"
        "<div>" + summary_html + "</div>"
        "<table style='width:100%;border-collapse:collapse;margin-top:12px;font-family:Arial,sans-serif;font-size:14px;'><thead>"
        "<tr style='text-align:left;font-size:13px;color:#666;'><th>#</th><th>Ticker</th><th>Reason</th></tr></thead><tbody>"
        + body_rows
        + "</tbody></table>"
        "<div style='margin-top:16px;'>" + disclaimer + "</div>"
        "<p style='font-size:12px;color:#999;font-family:Arial,sans-serif;'>Powered by Tarzan Screener</p>"
        "</div></body></html>"
    )


    text_lines = [template_name, "", *summary_lines, "", "Top picks:", ""]




    text_lines.extend([f"{i+1}. {row.get('ticker','')} - {row.get('reason','')}" for i, row in enumerate(rows[:50])])



    text_lines.append("")





    text_lines.append("Disclaimer: Historical performance is not indicative of future results.")



    return html, "\n".join(text_lines)
