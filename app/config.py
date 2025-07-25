import os

class Settings:
    # Đường dẫn đến cơ sở dữ liệu. Mặc định dùng SQLite với file recruitment.db
    # Nếu dùng PostgreSQL, bạn sẽ thay đổi nó thành chuỗi kết nối PostgreSQL của bạn.
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./recruitment.db")
    
    # KHÓA API của OpenAI để sử dụng GPT. RẤT QUAN TRỌNG!
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Cấu hình gửi email (dùng cho thư mời, onboarding)
    EMAIL_HOST = os.getenv("EMAIL_HOST")        # Ví dụ: smtp.gmail.com
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587)) # Cổng SMTP, thường là 587
    EMAIL_USERNAME = os.getenv("EMAIL_USERNAME") # Email của bạn
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD") # Mật khẩu của email (Đối với Gmail, cần dùng "Mật khẩu ứng dụng")

# Tạo một đối tượng settings để chúng ta có thể truy cập các cài đặt này ở bất cứ đâu
settings = Settings()