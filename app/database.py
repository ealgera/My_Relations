from sqlmodel import SQLModel, create_engine, Session
# import os
from config import get_settings
from .logging_config import app_logger

settings = get_settings()
# app_logger.debug(f"Testmode is: {settings.TESTING}")

if settings.TESTING:
    DATABASE_URL = "sqlite:///./test.db"
else:
    DATABASE_URL = settings.DATABASE_URL

# app_logger.debug(f"Database URL: {DATABASE_URL}")

# Engine aanmaken
engine = create_engine(DATABASE_URL, echo=settings.DEBUG)

# Functie om de database tabellen aan te maken
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Functie om een database sessie te krijgen
def get_session():
    with Session(engine) as session:
        yield session