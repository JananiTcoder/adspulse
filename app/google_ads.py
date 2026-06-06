import logging
from datetime import date, timedelta
from .composio_client import execute

logger = logging.getLogger(__name__)


def _yesterday() -> str:
    return (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")


def _flatten_rows(data: dict) -> list:
    envs = data.get("results") or []
    rows = []
    for env in envs:
        chunk = (env.get("response") or {}).get("data") or {}
        rows.extend(chunk.get("results") or [])
    return rows


def fetch_campaign_metrics(customer_id: str) -> dict:
    yesterday = _yesterday()
    gaql = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign_budget.amount_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.average_cpc
        FROM campaign
        WHERE segments.date BETWEEN '{yesterday}' AND '{yesterday}'
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
        LIMIT 50
    """
    logger.info("Fetching Google Ads data for customer %s on %s", customer_id, yesterday)
    raw = execute(
        action="GOOGLEADS_SEARCH_STREAM_GAQL",
        params={"query": gaql.strip()},
    )
    rows = _flatten_rows(raw)
    campaigns = []
    total_clicks = total_impressions = total_cost_micros = 0
    total_conversions = 0.0

    for row in rows:
        m = row.get("metrics") or {}
        c = row.get("campaign") or {}
        b = row.get("campaignBudget") or {}
        clicks = int(m.get("clicks") or 0)
        impressions = int(m.get("impressions") or 0)
        cost_micros = int(m.get("costMicros") or 0)
        conversions = float(m.get("conversions") or 0)
        avg_cpc_micros = int(m.get("averageCpc") or 0)
        budget_micros = int(b.get("amountMicros") or 0)
        spend = cost_micros / 1_000_000
        avg_cpc = avg_cpc_micros / 1_000_000
        ctr = (clicks / impressions * 100) if impressions > 0 else 0.0
        budget_usd = budget_micros / 1_000_000
        total_clicks += clicks
        total_impressions += impressions
        total_cost_micros += cost_micros
        total_conversions += conversions
        campaigns.append({
            "id": c.get("id", ""),
            "name": c.get("name", "Unknown Campaign"),
            "status": c.get("status", "UNKNOWN"),
            "spend": round(spend, 2),
            "clicks": clicks,
            "impressions": impressions,
            "conversions": round(conversions, 1),
            "ctr": round(ctr, 2),
            "avg_cpc": round(avg_cpc, 2),
            "budget": round(budget_usd, 2),
        })

    total_spend = total_cost_micros / 1_000_000
    total_avg_cpc = (total_cost_micros / total_clicks / 1_000_000) if total_clicks > 0 else 0.0
    return {
        "date": yesterday,
        "customer_id": customer_id,
        "summary": {
            "total_spend": round(total_spend, 2),
            "total_clicks": total_clicks,
            "total_impressions": total_impressions,
            "total_conversions": round(total_conversions, 1),
            "avg_cpc": round(total_avg_cpc, 2),
            "campaign_count": len(campaigns),
        },
        "campaigns": campaigns,
    }


def detect_anomalies(campaigns: list) -> list:
    anomalies = []
    if not campaigns:
        return anomalies
    avg_ctr = sum(c["ctr"] for c in campaigns) / len(campaigns)
    for c in campaigns:
        if c["spend"] > 20 and c["conversions"] == 0:
            anomalies.append({"type": "budget_waste", "campaign": c["name"],
                              "detail": f"${c['spend']:.2f} spent, 0 conversions", "severity": "warning"})
        if avg_ctr > 0 and c["ctr"] >= avg_ctr * 2 and c["clicks"] > 10:
            anomalies.append({"type": "winning", "campaign": c["name"],
                              "detail": f"{c['ctr']:.1f}% CTR (2x account average)", "severity": "positive"})
        if c["budget"] > 0 and c["spend"] >= c["budget"] * 0.9:
            anomalies.append({"type": "budget_cap", "campaign": c["name"],
                              "detail": f"${c['spend']:.2f} of ${c['budget']:.2f} daily budget used", "severity": "info"})
    return anomalies
