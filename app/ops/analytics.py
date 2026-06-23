from app.database.session import SessionLocal

class OpsAnalytics:
    """Basic usage analytics for ZyraXis ops layer."""

    def get_daily_usage(self, telegram_id: str):
        db = SessionLocal()
        try:
            result = db.execute(
                "SELECT ai_requests FROM usage WHERE telegram_id = :tid",
                {"tid": telegram_id}
            ).fetchone()

            return result[0] if result else 0
        finally:
            db.close()

    def get_total_users(self):
        db = SessionLocal()
        try:
            result = db.execute("SELECT COUNT(*) FROM users").fetchone()
            return result[0]
        finally:
            db.close()