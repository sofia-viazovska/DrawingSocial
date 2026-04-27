import re
from app.domain.models.models import User, Drawing
from app.domain.repositories.interfaces import UserRepository
from app.domain.exceptions.exceptions import (
    InvalidEmailError, 
    EmailAlreadyExistsError, 
    NicknameAlreadyExistsError,
    InvariantViolationError
)

class DomainFactory:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def create_user(self, email: str, nickname: str, hashed_password: str) -> User:
        # Simple invariant: valid email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise InvalidEmailError(f"Invalid email format: {email}")

        if not nickname:
            raise InvariantViolationError("Nickname cannot be empty")

        # Complex invariants: uniqueness (requires repository)
        if self.user_repo.get_by_email(email):
            raise EmailAlreadyExistsError(f"Email {email} is already in use")
        
        if self.user_repo.get_by_nickname(nickname):
            raise NicknameAlreadyExistsError(f"Nickname {nickname} is already in use")

        return User(
            id=None,
            email=email,
            nickname=nickname,
            hashed_password=hashed_password
        )

    def create_drawing(self, owner_id: int, title: str) -> Drawing:
        if not title:
            raise InvariantViolationError("Drawing title cannot be empty")
        
        return Drawing(
            id=None,
            owner_id=owner_id,
            title=title
        )
