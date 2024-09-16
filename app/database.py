from sqlmodel import SQLModel, create_engine, Session
from config import get_settings
from .logging_config import app_logger

settings = get_settings()

DATABASE_URL = settings.DATABASE_URL

# Engine aanmaken
engine = create_engine(DATABASE_URL, echo=False) #echo=settings.DEVELOPMENT)

# Functie om de database tabellen aan te maken
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Functie om een database sessie te krijgen
def get_session():
    with Session(engine) as session:    
        yield session