import time
from fastapi import APIRouter

router = APIRouter()

@router.get("/debug/system")
def system_debug():
    return {
        "status": "debug-active",
        "timestamp": int(time.time())
    }
