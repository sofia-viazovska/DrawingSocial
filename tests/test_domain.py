import pytest
from app.domain.models.models import User, Drawing
from app.domain.factories.factories import DomainFactory
from app.domain.exceptions.exceptions import InvariantViolationError, InvalidEmailError
from unittest.mock import MagicMock

def test_user_creation_validates_email():
    user_repo = MagicMock()
    user_repo.get_by_email.return_value = None
    user_repo.get_by_nickname.return_value = None
    factory = DomainFactory(user_repo)
    
    with pytest.raises(InvalidEmailError):
        factory.create_user("invalid-email", "nick", "hash")

def test_user_creation_validates_uniqueness():
    user_repo = MagicMock()
    user_repo.get_by_email.return_value = User(1, "exists@test.com", "nick", "hash")
    factory = DomainFactory(user_repo)
    
    with pytest.raises(InvariantViolationError): # EmailAlreadyExistsError inherits it
        factory.create_user("exists@test.com", "new-nick", "hash")

def test_user_follow_self_not_allowed():
    user = User(1, "test@test.com", "nick", "hash")
    with pytest.raises(InvariantViolationError):
        user.follow(1)

def test_drawing_add_layer_validates_data():
    drawing = Drawing(1, 1, "Title")
    with pytest.raises(InvariantViolationError):
        drawing.add_layer(1, "") # Empty image data

def test_drawing_toggle_like():
    drawing = Drawing(1, 1, "Title")
    drawing.toggle_like(10)
    assert 10 in drawing.likes
    drawing.toggle_like(10)
    assert 10 not in drawing.likes
