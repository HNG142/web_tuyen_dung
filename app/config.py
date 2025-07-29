import os

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recruitment.db")
  
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
  
    EMAIL_HOST = os.getenv("EMAIL_HOST")        
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587)) 
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME") 
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") 

settings = Settings()