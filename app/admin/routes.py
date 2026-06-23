from fastapi import APIRouter
from app.database.session import SessionLocal
from app.ops.event_store import EventLog
from app.database.models import User, Usage

router = APIRouter()

@router.get("/stats")
def stats():
    db = SessionLocal()

    try:
        total_users = db.query(User).count()

        ai_success = db.query(EventLog).filter_by(event_type="ai_success").count()
        ai_errors = db.query(EventLog).filter_by(event_type="ai_error").count()
        quota_denied = db.query(EventLog).filter_by(event_type="quota_denied").count()

        total_requests = db.query(Usage).count()

        return {
            "users": total_users,
            "ai_success": ai_success,
            "ai_errors": ai_errors,
            "quota_denied": quota_denied,
            "usage_rows": total_requests
        }

    finally:
        db.close()
