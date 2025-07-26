from fastapi import FastAPI # Khung web FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_db_and_tables # Import hàm tạo bảng DB
from fastapi.staticfiles import StaticFiles # Để phục vụ các file tĩnh (CSS, JS)
from fastapi.responses import HTMLResponse # Để trả về các trang HTML
from fastapi.templating import Jinja2Templates # Để render các template HTML
from dotenv import load_dotenv # Để tải các biến môi trường từ file .env
import os # Để tương tác với hệ điều hành

from app.database import create_db_and_tables # Hàm tạo bảng DB
from app.routers import candidates, interview, tests, auth # Nhập các router đã tạo

load_dotenv() # Tải các biến môi trường từ file .env ngay khi ứng dụng khởi động

app = FastAPI(
    title="Ứng dụng Tuyển dụng AI",
    description="Ứng dụng tuyển dụng tích hợp AI cho phép ứng viên nộp CV/JD, phỏng vấn sơ bộ, kiểm tra kỹ năng và quản lý quá trình tuyển dụng.",
    version="1.0.0",
)

# Gắn thư mục 'static' để phục vụ các file CSS, JavaScript, hình ảnh
# Khi bạn truy cập /static/css/style.css, nó sẽ lấy file từ thư mục static/css/style.css
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cấu hình Jinja2Templates để render các file HTML trong thư mục 'templates'
templates = Jinja2Templates(directory="templates")

# Bao gồm các router vào ứng dụng chính
# Mỗi router sẽ xử lý các nhóm API cụ thể
app.include_router(auth.router, prefix="/api/auth", tags=["Xác thực"]) # API cho đăng ký/đăng nhập
app.include_router(candidates.router, prefix="/api/candidates", tags=["Ứng viên & So khớp CV/JD"]) # API quản lý ứng viên, tải CV/JD
app.include_router(interview.router, prefix="/api/interview", tags=["Phỏng vấn AI"]) # API cho chatbot phỏng vấn
app.include_router(tests.router, prefix="/api/tests", tags=["Kiểm tra kỹ năng"]) # API cho kiểm tra kỹ năng


@app.on_event("startup")
def on_startup():
    """Hàm này sẽ chạy khi ứng dụng khởi động."""
    create_db_and_tables() # Đảm bảo các bảng cơ sở dữ liệu được tạo

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def read_root():
    """Phục vụ trang frontend chính của ứng dụng (index.html)."""
    # Đọc nội dung file index.html và trả về
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn
    # Khởi động server Uvicorn
    # host="0.0.0.0" để ứng dụng có thể truy cập từ bên ngoài (nếu deploy)
    # port=8000 là cổng mặc định
    # reload=True để server tự động khởi động lại khi có thay đổi code (tiện cho phát triển)
    uvicorn.run(app, host="0.0.0.0", port=8000)
origins = [
    "https://*.anvil.app",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ----------------------------------------

# --- THÊM ĐOẠN CODE NÀY ĐỂ TẠO BẢNG KHI ỨNG DỤNG KHỞI ĐỘNG ---
@app.on_event("startup")
async def startup_event():
    print("Running startup event: Creating database and tables if they don't exist.")
    try:
        create_db_and_tables()
        print("Database and tables checked/created successfully.")
    except Exception as e:
        print(f"Error during database startup: {e}")
        # Tùy chọn: Log lỗi chi tiết hơn hoặc gửi thông báo
# -----------------------------------------------------------

# Các import và router khác của bạn
from app.routers import candidates, interview, tests, auth

app.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
app.include_router(interview.router, prefix="/interviews", tags=["interviews"])
app.include_router(tests.router, prefix="/tests", tags=["tests"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Recruitment App API!"}