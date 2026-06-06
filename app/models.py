from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    customer_id = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    date = Column(String, nullable=False)
    total_spend = Column(Float, default=0.0)
    total_clicks = Column(Integer, default=0)
    total_impressions = Column(Integer, default=0)
    total_conversions = Column(Float, default=0.0)
    avg_cpc = Column(Float, default=0.0)
    ai_narrative = Column(Text, nullable=True)
    email_status = Column(String, default="pending")
    raw_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
