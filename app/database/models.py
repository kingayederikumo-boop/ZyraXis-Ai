from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, index=True)
    is_premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Usage(Base):
    __tablename__ = "usage"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, index=True)
    date = Column(String)
    ai_requests = Column(Integer, default=0)
