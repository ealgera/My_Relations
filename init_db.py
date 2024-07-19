# init_db.py
import os
from sqlmodel import SQLModel, create_engine, Session, text
from app.database import DATABASE_URL
from app.models.models import User, Families, Personen, Jubilea, Relatietypes, Relaties, Rollen  # Import all your models
from sqlalchemy.exc import OperationalError

from app.logging_config import app_logger

# Set up logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

def init_db():
    # Extract the database file path from the DATABASE_URL
    db_file = DATABASE_URL.replace("sqlite:///", "")
    
    # Check if the database file already exists
    if not os.path.exists(db_file):
        app_logger.info("Database does not exist. Creating new database and tables...")
        engine = create_engine(DATABASE_URL)
        SQLModel.metadata.create_all(engine)
        app_logger.info("Database and tables created successfully.")
    else:
        app_logger.info("Database already exists. Checking for missing tables...")
        engine = create_engine(DATABASE_URL)
        
        # Check for each table and create if it doesn't exist
        with Session(engine) as session:
            for table in SQLModel.metadata.sorted_tables:
                try:
                    # Use text() to wrap the SQL query
                    session.execute(text(f"SELECT * FROM {table.name} LIMIT 1"))
                    app_logger.info(f"Table '{table.name}' already exists.")
                except OperationalError:
                    app_logger.info(f"Table '{table.name}' does not exist. Creating...")
                    table.create(engine)
                    app_logger.info(f"Table '{table.name}' created successfully.")

if __name__ == "__main__":
    try:
        init_db()
        app_logger.info("Database initialization process completed successfully.")
    except Exception as e:
        app_logger.error(f"An error occurred during database initialization: {str(e)}")
        raise