from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class CallRecord:
    call_sid: str
    caller_name: str = ""
    community: str = ""
    phone: str = ""
    block: str = ""           # A, B, C, D
    resolution: str = ""      # "transfer", "email_sent", "whatsapp_sent", "note_taken"
    anger_level: str = "low"  # low, medium, high
    created_at: datetime = field(default_factory=datetime.now)
