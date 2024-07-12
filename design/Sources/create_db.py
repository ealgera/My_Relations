from app.database import engine
from sqlmodel import SQLModel
import sys

def create_db():
    print("Python version:", sys.version)
    # print("SQLModel version:", SQLModel.__version__)
    print("Creating database and tables...")
    try:
        # Explicitly import models
        from app.models.models import Families, Personen, Jubilea, Relatietypes, Relaties
        
        # Print all subclasses of SQLModel
        print("SQLModel subclasses:")
        for cls in SQLModel.__subclasses__():
            print(f"- {cls.__name__}")
        
        # Print all tables that should be created
        print("Tables to be created:")
        for table in SQLModel.metadata.tables.values():
            print(f"- {table.name}")
        
        SQLModel.metadata.create_all(engine)
        print("Database and tables created successfully!")
        
        # Verify created tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        print("Actually created tables:")
        for table in created_tables:
            print(f"- {table}")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_db()