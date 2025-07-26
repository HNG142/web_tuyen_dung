import os
from sqlmodel import create_engine, SQLModel, Session
from sqlalchemy.engine import URL 
from dotenv import load_dotenv

load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recruitment.db")


original_parsed_url = URL.make_url(DATABASE_URL)


try:
    final_url = URL.create(
        drivername="postgresql+psycopg_binary", 
        username=original_parsed_url.username,
        password=original_parsed_url.password,
        host=original_parsed_url.host,
        port=original_parsed_url.port,
        database=original_parsed_url.database,
        query=original_parsed_url.query 
    )
except AttributeError as e:
 
    print(f"Error creating final URL: {e}")

    raise 

engine = create_engine(final_url, echo=True)

def create_db_and_tables():
    print("Creating database and tables...")
    SQLModel.metadata.create_all(engine)
    print("Database and tables created.")

def get_session():
    with Session(engine) as session:
            yield session