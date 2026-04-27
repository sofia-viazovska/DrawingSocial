from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass(frozen=True)
class UserReadModel:
    id: int
    email: str
    nickname: str

@dataclass(frozen=True)
class LayerReadModel:
    id: int
    drawing_id: int
    author_id: int
    author_nickname: Optional[str]
    image_data: str
    created_at: datetime

@dataclass(frozen=True)
class DrawingReadModel:
    id: int
    owner_id: int
    owner_email: Optional[str]
    owner_nickname: Optional[str]
    title: str
    created_at: datetime
    layers: List[LayerReadModel]
    likes_count: int
