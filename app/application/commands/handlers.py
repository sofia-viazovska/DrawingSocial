from dataclasses import dataclass
from typing import Optional
from app.domain.models.models import User, Drawing
from app.domain.repositories.interfaces import UserRepository, DrawingRepository
from app.domain.factories.factories import DomainFactory
from app.domain.exceptions.exceptions import InvariantViolationError, EntityNotFoundError

# === ДОДАНО ДЛЯ ЛАБОРАТОРНОЇ 4 ===
from app.domain.events.events import DrawingCreatedEvent
from app.infrastructure.events.bus import event_bus

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
        if self.user_repo.get_by_email(command.email):
            raise InvariantViolationError(f"Email {command.email} is already registered")
        if self.user_repo.get_by_nickname(command.nickname):
            raise InvariantViolationError(f"Nickname {command.nickname} is already taken")
        
        user = self.factory.create_user(command.email, command.nickname, command.hashed_password)
        saved_user = self.user_repo.save(user)
        return saved_user.id

@dataclass(frozen=True)
class CreateDrawingCommand:
    owner_id: int
    title: str
    first_layer_data: str

class CreateDrawingHandler:
    def __init__(self, drawing_repo: DrawingRepository, factory: DomainFactory):
        self.drawing_repo = drawing_repo
        self.factory = factory

    def handle(self, command: CreateDrawingCommand) -> int:
        # 1. Основна бізнес-логіка (Домен)
        drawing = self.factory.create_drawing(command.owner_id, command.title)
        saved_drawing = self.drawing_repo.save(drawing)
        
        if command.first_layer_data:
            layer = saved_drawing.add_layer(command.owner_id, command.first_layer_data)
            self.drawing_repo.save(saved_drawing)

        # ==========================================
        # 2. ПОБІЧНІ ОПЕРАЦІЇ (Side Effects) - Лаба 4
        # ==========================================
        # Публікуємо подію в шину (Асинхронний підхід, слабка зв'язність)
        event = DrawingCreatedEvent(
            drawing_id=saved_drawing.id,
            owner_id=command.owner_id,
            title=command.title
        )
        event_bus.publish(event)

        return saved_drawing.id

@dataclass(frozen=True)
class AddLayerCommand:
    drawing_id: int
    user_id: int
    image_data: str

class AddLayerHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, command: AddLayerCommand) -> int:
        drawing = self.drawing_repo.get_by_id(command.drawing_id)
        if not drawing:
            raise EntityNotFoundError("Drawing not found")
        layer = drawing.add_layer(command.user_id, command.image_data)
        self.drawing_repo.save(drawing)
        return layer.id

@dataclass(frozen=True)
class ToggleLikeCommand:
    drawing_id: int
    user_id: int

class ToggleLikeHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, command: ToggleLikeCommand) -> None:
        drawing = self.drawing_repo.get_by_id(command.drawing_id)
        if not drawing:
            raise EntityNotFoundError("Drawing not found")
        drawing.toggle_like(command.user_id)
        self.drawing_repo.save(drawing)

@dataclass(frozen=True)
class DeleteDrawingCommand:
    drawing_id: int
    user_id: int

class DeleteDrawingHandler:
    def __init__(self, drawing_repo: DrawingRepository):
        self.drawing_repo = drawing_repo

    def handle(self, command: DeleteDrawingCommand) -> None:
        drawing = self.drawing_repo.get_by_id(command.drawing_id)
        if not drawing:
            raise EntityNotFoundError("Drawing not found")
        if drawing.owner_id != command.user_id:
            raise InvariantViolationError("Only the owner can delete this drawing")
        self.drawing_repo.delete(command.drawing_id)

@dataclass(frozen=True)
class FollowUserCommand:
    follower_id: int
    followed_id: int

class FollowUserHandler:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def handle(self, command: FollowUserCommand) -> None:
        if command.follower_id == command.followed_id:
            raise InvariantViolationError("You cannot follow yourself")
        self.user_repo.add_follow(command.follower_id, command.followed_id)

@dataclass(frozen=True)
class UnfollowUserCommand:
    follower_id: int
    followed_id: int

class UnfollowUserHandler:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def handle(self, command: UnfollowUserCommand) -> None:
        self.user_repo.remove_follow(command.follower_id, command.followed_id)
