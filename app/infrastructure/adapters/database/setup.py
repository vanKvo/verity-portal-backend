from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Allows the function to "pause" while the app uses the database to execute crud data, then resume to 
# run the cleanup code (db.close()) once the operation is done.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
