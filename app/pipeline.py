import json
import logging
from datetime import date
from sqlalchemy.orm import Session
from .models import User, Report
from .google_ads import fetch_campaign_metrics, detect_anomalies
from .ai_narrative import generate_narrative
from .email_sender import send_report

logger = logging.getLogger(__name__)


def run_for_user(user: User, db: Session) -> dict:
    today = date.today().strftime("%Y-%m-%d")
    result = {"user_id": user.id, "email": user.email, "status": "pending", "error": None}

    existing = db.query(Report).filter(
        Report.user_id == user.id, Report.date == today
    ).first()
    if existing and existing.email_status == "sent":
        result["status"] = "skipped_already_sent"
        return result

    report = existing or Report(user_id=user.id, date=today)
    if not existing:
        db.add(report)
        db.flush()

    try:
        logger.info("[%s] Fetching Google Ads data (customer %s)", user.email, user.customer_id)
        metrics = fetch_campaign_metrics(user.customer_id)
        s = metrics["summary"]
        report.total_spend = s["total_spend"]
        report.total_clicks = s["total_clicks"]
        report.total_impressions = s["total_impressions"]
        report.total_conversions = s["total_conversions"]
        report.avg_cpc = s["avg_cpc"]
        report.raw_data = json.dumps(metrics)

        anomalies = detect_anomalies(metrics["campaigns"])

        logger.info("[%s] Generating AI narrative", user.email)
        narrative = generate_narrative(metrics, anomalies)
        report.ai_narrative = narrative

        logger.info("[%s] Sending report email", user.email)
        sent = send_report(user.email, user.company_name, metrics, anomalies, narrative)
        report.email_status = "sent" if sent else "failed"
        db.commit()

        result["status"] = "success" if sent else "email_failed"
        result["spend"] = s["total_spend"]
        result["campaigns"] = s["campaign_count"]

    except Exception as exc:
        logger.exception("[%s] Pipeline error: %s", user.email, exc)
        report.email_status = "failed"
        db.commit()
        result["status"] = "error"
        result["error"] = str(exc)

    return result


def run_all(db: Session) -> list:
    users = db.query(User).filter(User.is_active == True).all()
    logger.info("Running daily pipeline for %d users", len(users))
    return [run_for_user(u, db) for u in users]
