import pytest
from src.models.user import User

def test_user_password_hashing():
    user = User(username="alice")
    user.set_password("secret123")
    assert user.check_password("secret123")
    assert not user.check_password("wrong")

def test_user_to_dict():
    user = User(id=1, username="alice")
    assert user.to_dict() == {"id": 1, "username": "alice"}
