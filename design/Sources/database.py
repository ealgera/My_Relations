from sqlmodel import SQLModel, create_engine, Session
# from .models import *  # Dit importeert alle modellen die we hebben gedefinieerd
# from .models.models import Families, Personen, Jubilea, Relatietypes, Relaties
import os

# Gebruik een omgevingsvariabele om te bepalen of we in test mode zijn
is_test = os.getenv('TESTING', 'False').lower() == 'true'

if is_test:
    DATABASE_URL = "sqlite:///./test.db"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./my_relations_app.db")

# Database URL (gebruik een omgevingsvariabele voor de productie)
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./my_relations_app.db")

# Engine aanmaken
engine = create_engine(DATABASE_URL, echo=True)

# Functie om de database tabellen aan te maken
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Functie om een database sessie te krijgen
def get_session():
    with Session(engine) as session:
        yield session