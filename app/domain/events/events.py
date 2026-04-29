from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass(frozen=True)
class DrawingCreatedEvent:
    """Integration Event: публікується, коли юзер створює новий малюнок"""
    drawing_id: int
    owner_id: int
    title: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
