from app.orchestrator.router import Orchestrator

# Central orchestrator instance (shared across transports)
_orchestrator = Orchestrator()


def handle_user(user_id: str, text: str) -> str:
    """
    Core execution boundary for all inbound messages.
    Transport-agnostic business logic entry.
    """
    return _orchestrator.handle(user_id, text)
