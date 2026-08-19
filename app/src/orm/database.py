from config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base

# Database URL - you can modify this based on your database setup
# For SQLite (development):
# DATABASE_URL = "sqlite:///./eyestock.db"
DATABASE_URL = settings.DATABASE_URL

# Create engine
engine = create_engine(DATABASE_URL)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Create tables
def create_tables():
    # Drop all existing tables
    Base.metadata.drop_all(bind=engine)
    # Create all tables with new schema
    Base.metadata.create_all(bind=engine)


# Dependency to get database session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
