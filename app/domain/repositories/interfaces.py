from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.models import User, Drawing, Layer

class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_nickname(self, nickname: str) -> Optional[User]:
        pass

    @abstractmethod
    def save(self, user: User) -> User:
        pass

    @abstractmethod
    def add_follow(self, follower_id: int, following_id: int):
        pass

    @abstractmethod
    def remove_follow(self, follower_id: int, following_id: int):
        pass

    @abstractmethod
    def get_followers(self, user_id: int) -> List[User]:
        pass

class DrawingRepository(ABC):
    @abstractmethod
    def get_by_id(self, drawing_id: int) -> Optional[Drawing]:
        pass

    @abstractmethod
    def list_feed(self, user_id: int) -> List[Drawing]:
        pass

    @abstractmethod
    def search(self, q: str) -> dict:
        pass

    @abstractmethod
    def get_user_drawings(self, user_id: int) -> List[Drawing]:
        pass

    @abstractmethod
    def get_user_contributed_drawings(self, user_id: int) -> List[Drawing]:
        pass

    @abstractmethod
    def is_following(self, follower_id: int, following_id: int) -> bool:
        pass

    @abstractmethod
    def save(self, drawing: Drawing) -> Drawing:
        pass

    @abstractmethod
    def delete(self, drawing_id: int):
        pass

    @abstractmethod
    def add_layer(self, layer: Layer) -> Layer:
        pass

    @abstractmethod
    def toggle_like(self, drawing_id: int, user_id: int):
        pass
