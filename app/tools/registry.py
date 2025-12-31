from typing import Any, Dict

from app.services.memory import memory_get, memory_put
from app.services.scheduler import schedule_meeting
from app.services.whatsapp_client import send_whatsapp_text


# Import your real tool implementations:
# from app.services.memory import memory_get
# from app.services.scheduler import schedule_meeting
# etc.

def build_tools() -> Dict[str, Any]:
    return {
        "memory_get": memory_get,
        "memory_put": memory_put,
        "schedule_meeting": schedule_meeting,
        "send_whatsapp_text": send_whatsapp_text,
        # add more tools here...
    }
