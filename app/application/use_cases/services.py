from typing import List, Optional
from app.domain.repositories.interfaces import UserRepository, DrawingRepository
from app.domain.factories.factories import DomainFactory
from app.domain.models.models import User, Drawing, Layer
from app.domain.exceptions.exceptions import EntityNotFoundError

class UserUseCases:
    def __init__(self, user_repo: UserRepository, factory: DomainFactory):
        self.user_repo = user_repo
        self.factory = factory

    def register_user(self, email: str, nickname: str, hashed_password: str) -> User:
        user = self.factory.create_user(email, nickname, hashed_password)
        return self.user_repo.save(user)

    def get_user(self, user_id: int) -> User:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise EntityNotFoundError(f"User with id {user_id} not found")
        return user

    def follow_user(self, follower_id: int, following_id: int):
        follower = self.get_user(follower_id)
        following = self.get_user(following_id)
        
        follower.follow(following_id)
        self.user_repo.add_follow(follower_id, following_id)

    def unfollow_user(self, follower_id: int, following_id: int):
        follower = self.get_user(follower_id)
        follower.unfollow(following_id)
        self.user_repo.remove_follow(follower_id, following_id)

    def get_followers(self, user_id: int) -> List[User]:
        return self.user_repo.get_followers(user_id)

class DrawingUseCases:
    def __init__(self, drawing_repo: DrawingRepository, factory: DomainFactory):
        self.drawing_repo = drawing_repo
        self.factory = factory

    def create_drawing(self, owner_id: int, title: str) -> Drawing:
        drawing = self.factory.create_drawing(owner_id, title)
        return self.drawing_repo.save(drawing)

    def get_drawing(self, drawing_id: int) -> Drawing:
        drawing = self.drawing_repo.get_by_id(drawing_id)
        if not drawing:
            raise EntityNotFoundError(f"Drawing with id {drawing_id} not found")
        return drawing

    def add_layer(self, drawing_id: int, author_id: int, image_data: str) -> Layer:
        drawing = self.get_drawing(drawing_id)
        layer = drawing.add_layer(author_id, image_data)
        return self.drawing_repo.add_layer(layer)

    def toggle_like(self, drawing_id: int, user_id: int):
        drawing = self.get_drawing(drawing_id)
        # We allow toggle like, so no exception here anymore
        drawing.toggle_like(user_id)
        self.drawing_repo.toggle_like(drawing_id, user_id)

    def list_feed(self, user_id: int) -> List[Drawing]:
        return self.drawing_repo.list_feed(user_id)

    def search(self, q: str) -> dict:
        return self.drawing_repo.search(q)

    def get_user_drawings(self, user_id: int) -> List[Drawing]:
        return self.drawing_repo.get_user_drawings(user_id)

    def get_user_contributed_drawings(self, user_id: int) -> List[Drawing]:
        return self.drawing_repo.get_user_contributed_drawings(user_id)

    def is_following(self, follower_id: int, following_id: int) -> bool:
        return self.drawing_repo.is_following(follower_id, following_id)

    def delete_drawing(self, drawing_id: int, user_id: int):
        drawing = self.get_drawing(drawing_id)
        if drawing.owner_id != user_id:
            from app.domain.exceptions.exceptions import InvariantViolationError
            raise InvariantViolationError("Only owner can delete drawing")
        self.drawing_repo.delete(drawing_id)
