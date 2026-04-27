from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from app.domain.exceptions.exceptions import InvariantViolationError

@dataclass
class User:
    id: Optional[int]
    email: str
    nickname: str
    hashed_password: str
    drawings: List['Drawing'] = field(default_factory=list)
    following: List[int] = field(default_factory=list) # IDs of users being followed
    followers: List[int] = field(default_factory=list) # IDs of followers

    def follow(self, user_id: int):
        if user_id == self.id:
            raise InvariantViolationError("User cannot follow themselves")
        if user_id not in self.following:
            self.following.append(user_id)

    def unfollow(self, user_id: int):
        if user_id in self.following:
            self.following.remove(user_id)

@dataclass
class Layer:
    id: Optional[int]
    drawing_id: int
    author_id: int
    image_data: str
    author_nickname: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Drawing:
    id: Optional[int]
    owner_id: int
    title: str
    owner_nickname: Optional[str] = None
    owner_email: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    layers: List[Layer] = field(default_factory=list)
    likes: List[int] = field(default_factory=list) # User IDs who liked

    def add_layer(self, author_id: int, image_data: str):
        if not image_data:
            raise InvariantViolationError("Layer image data cannot be empty")
        layer = Layer(id=None, drawing_id=self.id, author_id=author_id, image_data=image_data)
        self.layers.append(layer)
        return layer

    def toggle_like(self, user_id: int):
        if user_id in self.likes:
            self.likes.remove(user_id)
        else:
            self.likes.append(user_id)
