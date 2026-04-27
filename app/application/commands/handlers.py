from dataclasses import dataclass
from typing import Optional
from app.domain.repositories.interfaces import UserRepository, DrawingRepository
from app.domain.factories.factories import DomainFactory
from app.domain.exceptions.exceptions import EntityNotFoundError, InvariantViolationError

@dataclass(frozen=True)
class RegisterUserCommand:
    email: str
    nickname: str
    hashed_password: str

class RegisterUserHandler:
    def __init__(self, user_repo: UserRepository, factory: DomainFactory):
        self.user_repo = user_repo
        self.factory = factory

    def handle(self, command: RegisterUserCommand) -> int:
        user = self.factory.create_user(command.email, command.nickname, command.hashed_password)
        saved_user = self.user_repo.save(user)
        return saved_user.id

@dataclass(frozen=True)
class FollowUserCommand:
    follower_id: int
    following_id: int

class FollowUserHandler:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def handle(self, command: FollowUserCommand):
        follower = self.user_repo.get_by_id(command.follower_id)
        if not follower:
            raise EntityNotFoundError(f"User {command.follower_id} not found")
        
        following = self.user_repo.get_by_id(command.following_id)
        if not following:
            raise EntityNotFoundError(f"User {command.following_id} not found")

        follower.follow(command.following_id)
        self.user_repo.add_follow(command.follower_id, command.following_id)

@dataclass(frozen=True)
class UnfollowUserCommand:
    follower_id: int
    following_id: int

class UnfollowUserHandler:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def handle(self, command: UnfollowUserCommand):
        follower = self.user_repo.get_by_id(command.follower_id)
        if not follower:
            raise EntityNotFoundError(f"User {command.follower_id} not found")
            
        follower.unfollow(command.following_id)
        self.user_repo.remove_follow(command.follower_id, command.following_id)

@dataclass(frozen=True)
class CreateDrawingCommand:
    owner_id: int
    title: str
    first_layer_data: Optional[str] = None

class CreateDrawingHandler:
    def __init__(self, drawing_repo: DrawingRepository, factory: DomainFactory):
        self.drawing_repo = drawing_repo
        self.factory = factory

    def handle(self, command: CreateDrawingCommand) -> int:
        drawing = self.factory.create_drawing(command.owner_id, command.title)
        saved_drawing = self.drawing_repo.save(drawing)
        
        if command.first_layer_data:
            layer = saved_drawing.add_layer(command.owner_id, command.first_layer_data)
            self.drawing_repo.add_layer(layer)
            
        return saved_drawing.id

@dataclass(frozen=True)
class AddLayerCommand:
    drawing_id: int
    author_id: int
    image_data: str

class AddLayerHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, command: AddLayerCommand) -> int:
        drawing = self.drawing_repo.get_by_id(command.drawing_id)
        if not drawing:
            raise EntityNotFoundError(f"Drawing {command.drawing_id} not found")
            
        layer = drawing.add_layer(command.author_id, command.image_data)
        saved_layer = self.drawing_repo.add_layer(layer)
        return saved_layer.id

@dataclass(frozen=True)
class ToggleLikeCommand:
    drawing_id: int
    user_id: int

class ToggleLikeHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, command: ToggleLikeCommand):
        drawing = self.drawing_repo.get_by_id(command.drawing_id)
        if not drawing:
            raise EntityNotFoundError(f"Drawing {command.drawing_id} not found")
            
        drawing.toggle_like(command.user_id)
        self.drawing_repo.toggle_like(command.drawing_id, command.user_id)

@dataclass(frozen=True)
class DeleteDrawingCommand:
    drawing_id: int
    user_id: int

class DeleteDrawingHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, command: DeleteDrawingCommand):
        drawing = self.drawing_repo.get_by_id(command.drawing_id)
        if not drawing:
            raise EntityNotFoundError(f"Drawing {command.drawing_id} not found")
            
        if drawing.owner_id != command.user_id:
            raise InvariantViolationError("Only owner can delete drawing")
            
        self.drawing_repo.delete(command.drawing_id)
