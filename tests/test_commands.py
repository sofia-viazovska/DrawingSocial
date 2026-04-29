import pytest
from unittest.mock import MagicMock
from app.application.commands.handlers import (
    RegisterUserCommand, RegisterUserHandler,
    FollowUserCommand, FollowUserHandler,
    CreateDrawingCommand, CreateDrawingHandler
)
from app.domain.models.models import User, Drawing

def test_register_user_command():
    user_repo = MagicMock()
    factory = MagicMock()
    
    user_to_save = User(None, "test@test.com", "nick", "hash")
    saved_user = User(1, "test@test.com", "nick", "hash")
    
    factory.create_user.return_value = user_to_save
    user_repo.save.return_value = saved_user
    
    handler = RegisterUserHandler(user_repo, factory)
    command = RegisterUserCommand("test@test.com", "nick", "hash")
    
    user_id = handler.handle(command)
    
    assert user_id == 1
    factory.create_user.assert_called_once_with("test@test.com", "nick", "hash")
    user_repo.save.assert_called_once_with(user_to_save)

def test_follow_user_command():
    user_repo = MagicMock()
    
    follower = User(1, "f@test.com", "follower", "hash")
    following = User(2, "s@test.com", "following", "hash")
    
    user_repo.get_by_id.side_effect = lambda uid: follower if uid == 1 else following
    
    handler = FollowUserHandler(user_repo)
    command = FollowUserCommand(1, 2)
    
    handler.handle(command)
    
    assert 2 in follower.following
    user_repo.add_follow.assert_called_once_with(1, 2)

def test_create_drawing_command():
    drawing_repo = MagicMock()
    factory = MagicMock()

    drawing_to_save = Drawing(None, 1, "Title")
    saved_drawing = Drawing(10, 1, "Title")

    factory.create_drawing.return_value = drawing_to_save
    drawing_repo.save.return_value = saved_drawing

    handler = CreateDrawingHandler(drawing_repo, factory)
    command = CreateDrawingCommand(1, "Title", "first_layer")

    drawing_id = handler.handle(command)

    # Хендлер: factory -> save (отримуємо ID) -> add_layer (домен) -> save (із шаром)
    assert drawing_id == 10
    factory.create_drawing.assert_called_once_with(1, "Title")
    assert drawing_repo.save.call_count == 2
    # Після другого save домен-об'єкт повинен містити перший шар
    assert len(saved_drawing.layers) == 1
    assert saved_drawing.layers[0].image_data == "first_layer"
