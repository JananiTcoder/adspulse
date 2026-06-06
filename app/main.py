import logging
import json
from datetime import date

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .database import engine, get_db
from . import models
from .pipeline import run_for_user, run_all
from .scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

app = FastAPI(title="AdsPulse", description="Daily Google Ads Intelligence")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

models.Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def startup():
    start_scheduler()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/register")
def register(
    request: Request,
    company_name: str = Form(...),
    email: str = Form(...),
    customer_id: str = Form(...),
    db: Session = Depends(get_db),
):
    clean_id = customer_id.replace("-", "").strip()
    if not clean_id.isdigit():
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "Please enter a valid Google Ads Customer ID (digits only, e.g. 531-300-6442).",
        })
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return RedirectResponse(f"/dashboard/{email}", status_code=302)
    user = models.User(company_name=company_name, email=email, customer_id=clean_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return templates.TemplateResponse("success.html", {
        "request": request, "company_name": company_name,
        "email": email, "user_id": user.id,
    })


@app.get("/dashboard/{email}", response_class=HTMLResponse)
def dashboard(request: Request, email: str, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return RedirectResponse("/")
    reports = (
        db.query(models.Report)
        .filter(models.Report.user_id == user.id)
        .order_by(models.Report.created_at.desc())
        .limit(30)
        .all()
    )
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "reports": reports})


@app.post("/generate/{user_id}")
def generate_now(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return run_for_user(user, db)


@app.post("/internal/run-daily")
def run_daily(db: Session = Depends(get_db)):
    results = run_all(db)
    success = sum(1 for r in results if r["status"] == "success")
    return {"processed": len(results), "success": success, "results": results}
