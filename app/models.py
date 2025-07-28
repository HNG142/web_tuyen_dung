from __future__ import annotations
from sqlmodel import Field, SQLModel, Relationship # Field để định nghĩa cột, Relationship để liên kết bảng
from typing import Optional, List # Các kiểu dữ liệu Python
from datetime import datetime # Để làm việc với thời gian
from pydantic import BaseModel, EmailStr

# Định nghĩa bảng User (người dùng hệ thống, ví dụ: nhà tuyển dụng)
class User(SQLModel, table=True): # table=True nghĩa là đây sẽ là một bảng trong DB
    id: Optional[int] = Field(default=None, primary_key=True) # ID tự tăng, khóa chính
    email: str = Field(unique=True, index=True) # Email phải là duy nhất, và được đánh chỉ mục để tìm kiếm nhanh
    hashed_password: str # Mật khẩu đã được mã hóa
    is_active: bool = Field(default=True) # Tài khoản có hoạt động không
    is_admin: bool = Field(default=False) # Có phải tài khoản quản trị không

    # Liên kết với bảng Candidate (Một User có thể quản lý nhiều Candidate)
    candidates: List["Candidate"] = Relationship(back_populates="user")

# Định nghĩa bảng MatchResult (kết quả so khớp CV-JD)
class MatchResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id") # Liên kết với Candidate
    candidate: Optional[Candidate] = Relationship(back_populates="match_results")
    
    jd_id: Optional[int] = None # Nếu bạn lưu JD vào một bảng riêng, có thể liên kết ở đây
    match_score: int # Điểm phù hợp (0-100)
    feedback: str # Phản hồi của AI
    suggestions: str # Gợi ý chỉnh sửa CV (lưu dưới dạng chuỗi JSON)
    created_at: datetime = Field(default_factory=datetime.utcnow) # Thời gian tạo

class MatchResultBase(SQLModel):
    match_score: int
    feedback: str
    suggestions: str
    created_at: datetime

class MatchResultCreate(MatchResultBase):
    pass

class MatchResultPublic(MatchResultBase):
    id: int

# Định nghĩa bảng Candidate (ứng viên)
class Candidate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id") # Liên kết với User
    user: Optional[User] = Relationship(back_populates="candidates") # Quan hệ ngược lại

    full_name: str
    email: str = Field(unique=True, index=True)
    phone_number: Optional[str] = None
    applied_position: Optional[str] = None # Vị trí ứng tuyển
    cv_text: Optional[str] = None # Lưu trữ văn bản trích xuất từ CV
    jd_text: Optional[str] = None # Lưu trữ văn bản mô tả công việc

    # Các mối quan hệ với các bảng khác (một ứng viên có nhiều kết quả phỏng vấn, kiểm tra...)
    interviews: List["Interview"] = Relationship(back_populates="candidate")
    skill_tests: List["SkillTestResult"] = Relationship(back_populates="candidate")
    match_results: List["MatchResult"] = Relationship(back_populates="candidate")

# Định nghĩa bảng Interview (kết quả phỏng vấn AI)
class Interview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id")
    candidate: Optional[Candidate] = Relationship(back_populates="interviews")

    session_id: str = Field(unique=True, index=True) # ID duy nhất cho phiên chatbot
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    overall_score: Optional[int] = None # Điểm tổng quan của buổi phỏng vấn (nếu có)
    overall_feedback: Optional[str] = None # Phản hồi tổng quan

# Định nghĩa bảng Question (câu hỏi trắc nghiệm kỹ năng)
class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question_text: str # Nội dung câu hỏi
    options: str # Các lựa chọn (lưu dưới dạng chuỗi JSON: ["A", "B", "C"])
    correct_answer: str # Đáp án đúng
    skill_category: str # Danh mục kỹ năng (ví dụ: "Python", "Database")

    test_results: List["SkillTestResultItem"] = Relationship(back_populates="question")

# Định nghĩa bảng SkillTestResult (kết quả tổng quan của một bài kiểm tra kỹ năng)
class SkillTestResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id")
    candidate: Optional[Candidate] = Relationship(back_populates="skill_tests")

    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    score: Optional[int] = None # Điểm tổng
    total_questions: Optional[int] = None # Tổng số câu hỏi

    items: List["SkillTestResultItem"] = Relationship(back_populates="test_result")

# Định nghĩa bảng SkillTestResultItem (chi tiết từng câu trả lời trong bài kiểm tra)
class SkillTestResultItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    test_result_id: int = Field(foreign_key="skilltestresult.id")
    test_result: Optional[SkillTestResult] = Relationship(back_populates="items")

    question_id: int = Field(foreign_key="question.id")
    question: Optional[Question] = Relationship(back_populates="test_results")
    
    selected_answer: Optional[str] # Đáp án ứng viên chọn
    is_correct: Optional[bool] # Có đúng không

class User(BaseModel):
    email: EmailStr

user = User(email="test@example.com")
print(user.email)