import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.infrastructure.adapters.database.setup import Base
from app.infrastructure.adapters.database.models import UserModel
from app.domain.models.user import User

@pytest.fixture(scope="module")
def engine():
    return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="module")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

def test_create_user_model(db_session):
    domain_user = User.create(email="test@corporate.com", raw_password="password")
    
    db_user = UserModel(
        email=domain_user.email,
        hashed_password=domain_user.hashed_password,
        role=domain_user.role,
        is_active=domain_user.is_active
    )
    
    db_session.add(db_user)
    db_session.commit()
    
    saved_user = db_session.query(UserModel).filter_by(email="test@corporate.com").first()
    assert saved_user is not None
    assert saved_user.email == "test@corporate.com"
    assert saved_user.hashed_password == domain_user.hashed_password
    assert saved_user.role == "user"
