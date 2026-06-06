import logging
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
def home(request: Request, db: Session = Depends(get_db), added: str = None, error: str = None):
    users = (
        db.query(models.User)
        .filter(models.User.is_active == True)
        .order_by(models.User.created_at.desc())
        .all()
    )
    last_reports = {}
    for user in users:
        report = (
            db.query(models.Report)
            .filter(models.Report.user_id == user.id)
            .order_by(models.Report.created_at.desc())
            .first()
        )
        last_reports[user.id] = report

    return templates.TemplateResponse("index.html", {
        "request": request,
        "users": users,
        "last_reports": last_reports,
        "added": added,
        "error": error,
    })


@app.post("/add-client")
def add_client(
    request: Request,
    company_name: str = Form(...),
    email: str = Form(...),
    customer_id: str = Form(...),
    db: Session = Depends(get_db),
):
    clean_id = customer_id.replace("-", "").strip()
    if not clean_id.isdigit():
        return RedirectResponse("/?error=Invalid+Customer+ID+format", status_code=302)

    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return RedirectResponse(f"/?error=Email+already+registered", status_code=302)

    user = models.User(company_name=company_name, email=email, customer_id=clean_id)
    db.add(user)
    db.commit()
    return RedirectResponse(f"/?added={company_name}", status_code=302)


@app.post("/remove-client/{user_id}")
def remove_client(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.is_active = False
        db.commit()
    return RedirectResponse("/", status_code=302)


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
