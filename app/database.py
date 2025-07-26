import os
from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv

load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recruitment.db")

connection_string = DATABASE_URL
if connection_string.startswith("postgresql://"):
    connection_string = connection_string.replace("postgresql://", "postgresql+psycopg_binary://")
elif connection_string.startswith("postgres://"):
    connection_string = connection_string.replace("postgres://", "postgresql+psycopg_binary://")
engine = create_engine(connection_string, echo=True)

def create_db_and_tables():
    print("Running startup event: Creating database and tables if they don't exist.")
    try:
        SQLModel.metadata.create_all(engine)
        print("Database and tables checked/created successfully.")
    except Exception as e:
        print(f"Error during database startup: {e}")
        raise 

def get_session():
    with Session(engine) as session:
            yield session