from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Usage(Base):
    __tablename__ = "usage"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, index=True)
    date = Column(String)

    ai_requests = Column(Integer, default=0)
    roleplay_requests = Column(Integer, default=0)
    image_requests = Column(Integer, default=0)
