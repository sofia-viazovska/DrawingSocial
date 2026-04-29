from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models.models import User, Drawing

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
    def add_follow(self, follower_id: int, followed_id: int) -> None:
        pass

    @abstractmethod
    def remove_follow(self, follower_id: int, followed_id: int) -> None:
        pass

class DrawingRepository(ABC):
    @abstractmethod
    def get_by_id(self, drawing_id: int) -> Optional[Drawing]:
        pass

    @abstractmethod
    def save(self, drawing: Drawing) -> Drawing:
        pass

    @abstractmethod
    def delete(self, drawing_id: int) -> None:
        pass
