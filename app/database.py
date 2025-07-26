import os
from sqlmodel import create_engine, SQLModel, Session
from dotenv import load_dotenv

# Tải biến môi trường từ .env (chỉ cho môi trường phát triển cục bộ)
# Trên Heroku, biến môi trường sẽ được Heroku cung cấp trực tiếp
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recruitment.db")

# Đối với SQLite
# engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False})

# Đối với PostgreSQL (khuyến nghị trên Heroku)
engine = create_engine(DATABASE_URL.replace("postgresql://", "postgresql+psycopg_binary://"), echo=True)

def create_db_and_tables():
    print("Creating database and tables...")
    SQLModel.metadata.create_all(engine)
    print("Database and tables created.")

def get_session():
    with Session(engine) as session:
        yield session