from fastapi import APIRouter, Depends, HTTPException, status # Các công cụ của FastAPI
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm # Hỗ trợ đăng nhập OAuth2
from datetime import datetime, timedelta # Để làm việc với thời gian hết hạn của token
from typing import Annotated # Hỗ trợ kiểu dữ liệu mới trong Python

from passlib.context import CryptContext # Để mã hóa và kiểm tra mật khẩu
from jose import JWTError, jwt # Để tạo và giải mã JWT (JSON Web Token)

from sqlmodel import Session, select # Các công cụ của SQLModel
from app.database import get_session # Lấy phiên làm việc với DB
from app.models import User # Model User
from app.schemas import UserCreate, UserPublic, Token, TokenData # Schemas cho User và Token
from app.config import settings # Nhập cài đặt (có thể thêm SECRET_KEY vào config sau)

router = APIRouter()

# --- Cấu hình JWT (Token xác thực) ---
# KHÓA BÍ MẬT này phải được giữ kín và không được chia sẻ công khai!
# Trong thực tế, bạn nên đặt nó trong file .env và đọc từ settings.
SECRET_KEY = "day_la_mot_khoa_bi_mat_rat_manh_me_va_dai_de_bao_mat_token_cua_ban" # THAY THẾ BẰNG MỘT CHUỖI NGẪU NHIÊN VÀ DÀI!
ALGORITHM = "HS256" # Thuật toán mã hóa JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # Thời gian hết hạn của token (tính bằng phút)

# Đối tượng để mã hóa/giải mã mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# Đối tượng để FastAPI hiểu cách lấy token từ Header (Authorization: Bearer <token>)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain_password, hashed_password):
    """Kiểm tra mật khẩu người dùng nhập vào có khớp với mật khẩu đã mã hóa không."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Mã hóa mật khẩu."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Tạo một Access Token (JWT)."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15) # Mặc định 15 phút
    to_encode.update({"exp": expire}) # Thêm thời gian hết hạn vào token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # Mã hóa token
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_session)):
    """
    Hàm này được dùng làm Dependency (phụ thuộc) cho các API cần xác thực.
    Nó giải mã token, kiểm tra tính hợp lệ và trả về thông tin người dùng hiện tại.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Không thể xác thực thông tin đăng nhập",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]) # Giải mã token
        email: str = payload.get("sub") # Lấy email từ payload
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError: # Nếu token không hợp lệ
        raise credentials_exception
    user = db.exec(select(User).where(User.email == token_data.email)).first() # Tìm người dùng trong DB
    if user is None:
        raise credentials_exception
    return user

# --- API Endpoints cho Xác thực ---
@router.post("/register", response_model=UserPublic)
async def register_user(user: UserCreate, db: Session = Depends(get_session)):
    """API để đăng ký người dùng mới (ví dụ: nhà tuyển dụng)."""
    existing_user = db.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã được đăng ký.")
    
    hashed_password = get_password_hash(user.password) # Mã hóa mật khẩu
    new_user = User(email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user) # Cập nhật đối tượng user với ID từ DB
    return new_user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], # Dữ liệu đăng nhập (username, password)
    db: Session = Depends(get_session)
):
    """API để đăng nhập và lấy Access Token."""
    user = db.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai email hoặc mật khẩu.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users/me/", response_model=UserPublic)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """API để lấy thông tin người dùng hiện tại (cần xác thực)."""
    return current_user