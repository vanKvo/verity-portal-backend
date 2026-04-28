import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.infrastructure.adapters.database.setup import get_db, Base
from app.domain.models.user import User
from app.infrastructure.adapters.database.models import UserModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Set up in-memory DB for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def run_around_tests():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_register_user():
    response = client.post("/auth/register", json={"email": "newuser@corporate.com", "password": "password"})
    assert response.status_code == 201
    assert "access_token" in response.json()

def test_register_invalid_domain():
    response = client.post("/auth/register", json={"email": "newuser@gmail.com", "password": "password"})
    assert response.status_code == 400

def test_login_user():
    # First register
    client.post("/auth/register", json={"email": "loginuser@corporate.com", "password": "password"})
    
    # Then login
    response = client.post("/auth/login", data={"username": "loginuser@corporate.com", "password": "password"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_invalid_password():
    client.post("/auth/register", json={"email": "loginuser2@corporate.com", "password": "password"})
    response = client.post("/auth/login", data={"username": "loginuser2@corporate.com", "password": "wrongpassword"})
    assert response.status_code == 401

def test_guest_login():
    response = client.post("/auth/guest-login")
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["role"] == "guest"
