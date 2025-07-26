import os
from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv
from sqlalchemy.engine import URL 

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recruitment.db")

parsed_url = URL.create.from_string(DATABASE_URL)
if parsed_url.drivername == "psycopg2": 
    parsed_url.drivername = "psycopg_binary"
elif parsed_url.drivername == "postgresql":
    parsed_url.drivername = "postgresql+psycopg_binary" 
elif parsed_url.drivername == "postgresql+psycopg":
    parsed_url.drivername = "postgresql+psycopg_binary"


engine = create_engine(parsed_url, echo=True) 
# -----------------------------------------------------------

def create_db_and_tables():
    print("Creating database and tables...")
    SQLModel.metadata.create_all(engine)
    print("Database and tables created.")

def get_session():
    with Session(engine) as session:
        yield session