import pytest
from app.domain.models.user import User, InvalidDomainError

def test_create_user_hashes_password():
    user = User.create(email="test@corporate.com", raw_password="SecurePassword123!")
    
    assert user.email == "test@corporate.com"
    assert user.hashed_password != "SecurePassword123!"
    assert user.verify_password("SecurePassword123!") is True
    assert user.verify_password("WrongPassword") is False

def test_create_user_validates_domain():
    with pytest.raises(InvalidDomainError):
        User.create(email="hacker@gmail.com", raw_password="password")
