import os
from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv
from sqlalchemy.engine import make_url

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recruitment.db")
parsed_url = make_url(DATABASE_URL)

if parsed_url.drivername == "psycopg2": 
    parsed_url.drivername = "postgresql+psycopg_binary"
elif parsed_url.drivername == "postgresql":
    parsed_url.drivername = "postgresql+psycopg_binary" 
elif parsed_url.drivername == "postgresql+psycopg":
    parsed_url.drivername = "postgresql+psycopg_binary"


engine = create_engine(parsed_url, echo=True) 

def create_db_and_tables():
    print("Creating database and tables...")
    SQLModel.metadata.create_all(engine)
    print("Database and tables created.")

def get_session():
    with Session(engine) as session:
        yield session