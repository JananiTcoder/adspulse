# AdsPulse

AI-powered daily Google Ads monitoring platform. Sends plain-English campaign reports to your inbox every morning.

## Stack
- FastAPI + SQLAlchemy (Python)
- Composio (Google Ads data + Gmail sending)
- Claude Haiku (AI narrative)
- Render (hosting + cron)

## Setup
1. Copy `.env.example` → `.env` and fill in your API keys
2. `pip install -r requirements.txt`
3. `uvicorn app.main:app --reload`
