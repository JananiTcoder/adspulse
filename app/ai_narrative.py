import logging
from groq import Groq
from .config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a senior Google Ads analyst briefing a non-technical
business owner. Write in plain English — no jargon, no acronyms without explanation.

Rules:
1. Lead with the single most important insight (good or bad).
2. Explain WHY a metric changed, not just THAT it changed.
3. Give ONE specific, actionable recommendation at the end.
4. Maximum 220 words. No bullet points — flowing paragraphs only.
5. Sound like a trusted advisor, not a software tool.
6. Never say "as an AI". Never use unexplained terms like ROAS or CTR without defining them."""


def _build_prompt(metrics: dict, anomalies: list) -> str:
    s = metrics["summary"]
    camps = metrics["campaigns"][:5]
    camp_lines = "\n".join(
        f"  - {c['name']}: ${c['spend']:.2f} spend, {c['clicks']} clicks, "
        f"{c['conversions']} conversions, {c['ctr']:.1f}% click-through rate"
        for c in camps
    )
    anomaly_lines = ""
    if anomalies:
        anomaly_lines = "\nALERTS:\n" + "\n".join(
            f"  - [{a['severity'].upper()}] {a['campaign']}: {a['detail']}"
            for a in anomalies
        )
    return f"""Yesterday's Google Ads performance:

ACCOUNT TOTALS:
  Total spend: ${s['total_spend']:.2f}
  Clicks: {s['total_clicks']}
  Impressions: {s['total_impressions']}
  Conversions: {s['total_conversions']}
  Average cost per click: ${s['avg_cpc']:.2f}
  Active campaigns: {s['campaign_count']}

TOP CAMPAIGNS (by spend):
{camp_lines}
{anomaly_lines}

Write the executive briefing now. Start directly with the insight.""".strip()


def _fallback_narrative(metrics: dict, anomalies: list) -> str:
    s = metrics["summary"]
    waste = [a for a in anomalies if a["type"] == "budget_waste"]
    winners = [a for a in anomalies if a["type"] == "winning"]
    parts = [
        f"Yesterday your Google Ads account spent ${s['total_spend']:.2f} "
        f"across {s['campaign_count']} campaigns, generating {s['total_clicks']} clicks "
        f"and {s['total_conversions']} conversions."
    ]
    if waste:
        names = ", ".join(a["campaign"] for a in waste[:2])
        parts.append(f"Attention needed: {names} spent budget without conversions — consider pausing or restructuring.")
    if winners:
        names = ", ".join(a["campaign"] for a in winners[:2])
        parts.append(f"Strong performance: {names} is outperforming your account average — consider increasing its budget.")
    return " ".join(parts)


def generate_narrative(metrics: dict, anomalies: list) -> str:
    if not settings.GROQ_API_KEY:
        logger.warning("No GROQ_API_KEY — using fallback narrative")
        return _fallback_narrative(metrics, anomalies)
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=400,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _build_prompt(metrics, anomalies)},
            ],
        )
        return completion.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("Groq API error: %s — using fallback", exc)
        return _fallback_narrative(metrics, anomalies)
