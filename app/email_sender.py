import logging
from datetime import datetime
from .composio_client import execute

logger = logging.getLogger(__name__)
GMAIL_ACCOUNT_ID = "gmail_moter-worldy"


def _severity_emoji(anomalies: list) -> str:
    if any(a["severity"] == "warning" for a in anomalies):
        return "⚠️"
    if any(a["severity"] == "positive" for a in anomalies):
        return "\U0001f525"
    return "\U0001f4ca"


def _build_html(company: str, metrics: dict, anomalies: list, narrative: str) -> str:
    s = metrics["summary"]
    date_str = datetime.strptime(metrics["date"], "%Y-%m-%d").strftime("%B %d, %Y")
    campaigns_rows = ""
    for c in metrics["campaigns"][:6]:
        conv_color = "#16a34a" if c["conversions"] > 0 else "#dc2626"
        campaigns_rows += f"""
        <tr>
          <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;">{c['name']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;text-align:right;">${c['spend']:.2f}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;text-align:right;">{c['clicks']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;text-align:right;color:{conv_color};font-weight:600;">{c['conversions']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;text-align:right;">{c['ctr']:.1f}%</td>
        </tr>"""
    anomaly_blocks = ""
    for a in anomalies:
        if a["severity"] == "warning":
            bg, icon = "#fef9c3", "⚠️"
        elif a["severity"] == "positive":
            bg, icon = "#f0fdf4", "\U0001f525"
        else:
            bg, icon = "#eff6ff", "ℹ️"
        anomaly_blocks += f"""
        <div style="background:{bg};border-radius:8px;padding:12px 16px;margin:8px 0;font-size:14px;">
          {icon} <strong>{a['campaign']}</strong> — {a['detail']}
        </div>"""
    alerts_section = ""
    if anomalies:
        alerts_section = f"<tr><td style='padding:20px 32px 0;'><div style='font-size:13px;font-weight:600;color:#374151;margin-bottom:8px;'>ALERTS &amp; HIGHLIGHTS</div>{anomaly_blocks}</td></tr>"
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1);">
        <tr>
          <td style="background:linear-gradient(135deg,#4f46e5,#7c3aed);padding:32px;text-align:center;">
            <div style="font-size:13px;color:#c4b5fd;letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;">AdsPulse Daily Report</div>
            <div style="font-size:24px;font-weight:700;color:#ffffff;">{company}</div>
            <div style="font-size:14px;color:#ddd6fe;margin-top:4px;">{date_str}</div>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px 0;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td width="25%" style="text-align:center;padding:16px 8px;background:#f8fafc;border-radius:8px;">
                  <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Spend</div>
                  <div style="font-size:22px;font-weight:700;color:#1e293b;margin-top:4px;">${s['total_spend']:.2f}</div>
                </td>
                <td width="4%"></td>
                <td width="25%" style="text-align:center;padding:16px 8px;background:#f8fafc;border-radius:8px;">
                  <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Clicks</div>
                  <div style="font-size:22px;font-weight:700;color:#1e293b;margin-top:4px;">{s['total_clicks']:,}</div>
                </td>
                <td width="4%"></td>
                <td width="25%" style="text-align:center;padding:16px 8px;background:#f8fafc;border-radius:8px;">
                  <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Conversions</div>
                  <div style="font-size:22px;font-weight:700;color:#16a34a;margin-top:4px;">{s['total_conversions']}</div>
                </td>
                <td width="4%"></td>
                <td width="25%" style="text-align:center;padding:16px 8px;background:#f8fafc;border-radius:8px;">
                  <div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">Avg CPC</div>
                  <div style="font-size:22px;font-weight:700;color:#1e293b;margin-top:4px;">${s['avg_cpc']:.2f}</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 32px 0;">
            <div style="background:#f0f9ff;border-left:4px solid #4f46e5;border-radius:0 8px 8px 0;padding:20px 24px;">
              <div style="font-size:12px;color:#4f46e5;font-weight:600;letter-spacing:1px;text-transform:uppercase;margin-bottom:10px;">AI Analysis</div>
              <div style="font-size:15px;color:#1e293b;line-height:1.7;">{narrative}</div>
            </div>
          </td>
        </tr>
        {alerts_section}
        <tr>
          <td style="padding:24px 32px 0;">
            <div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:12px;">CAMPAIGNS</div>
            <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;font-size:13px;">
              <tr style="background:#f8fafc;">
                <th style="padding:10px 12px;text-align:left;color:#64748b;font-weight:600;">Campaign</th>
                <th style="padding:10px 12px;text-align:right;color:#64748b;font-weight:600;">Spend</th>
                <th style="padding:10px 12px;text-align:right;color:#64748b;font-weight:600;">Clicks</th>
                <th style="padding:10px 12px;text-align:right;color:#64748b;font-weight:600;">Conv.</th>
                <th style="padding:10px 12px;text-align:right;color:#64748b;font-weight:600;">CTR</th>
              </tr>
              {campaigns_rows}
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;text-align:center;color:#94a3b8;font-size:12px;border-top:1px solid #f1f5f9;margin-top:24px;">
            <div style="margin-top:16px;">Powered by <strong style="color:#4f46e5;">AdsPulse</strong> — Daily Google Ads Intelligence</div>
            <div style="margin-top:4px;">You're receiving this because you connected your Google Ads account.</div>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_report(to_email: str, company: str, metrics: dict, anomalies: list, narrative: str) -> bool:
    date_str = datetime.strptime(metrics["date"], "%Y-%m-%d").strftime("%B %d, %Y")
    emoji = _severity_emoji(anomalies)
    subject = f"{emoji} {company} — Google Ads Report for {date_str}"
    html_body = _build_html(company, metrics, anomalies, narrative)
    logger.info("Sending report to %s", to_email)
    try:
        execute(
            action="GMAIL_SEND_EMAIL",
            params={"recipient_email": to_email, "subject": subject, "body": html_body, "is_html": True},
            entity_id=GMAIL_ACCOUNT_ID,
        )
        logger.info("Email sent successfully to %s", to_email)
        return True
    except Exception as exc:
        logger.error("Failed to send email to %s: %s", to_email, exc)
        return False
