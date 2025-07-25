from pydantic import BaseModel, EmailStr # BaseModel để tạo schema, EmailStr để kiểm tra định dạng email
from typing import List, Optional, Dict # Các kiểu dữ liệu Python
from datetime import datetime # Để làm việc với thời gian

# --- Schema cho xác thực (Auth) ---
class UserCreate(BaseModel): # Dữ liệu khi tạo người dùng mới
    email: EmailStr
    password: str

class UserPublic(BaseModel): # Dữ liệu người dùng khi hiển thị công khai (không bao gồm mật khẩu)
    id: int
    email: EmailStr
    is_active: bool
    is_admin: bool

class Token(BaseModel): # Dữ liệu token sau khi đăng nhập thành công
    access_token: str
    token_type: str

class TokenData(BaseModel): # Dữ liệu được mã hóa bên trong token
    email: Optional[str] = None

# --- Schema cho ứng viên (Candidates) ---
class CandidateCreate(BaseModel): # Dữ liệu khi tạo ứng viên mới
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    applied_position: Optional[str] = None

class CandidatePublic(CandidateCreate): # Dữ liệu ứng viên khi hiển thị công khai (có thêm ID)
    id: int
    # Có thể thêm các quan hệ nếu bạn muốn hiển thị chi tiết khi lấy ứng viên
    match_results: Optional[List["MatchResultPublic"]] = None
    interviews: Optional[List["Interview"]] = None
    skill_tests: Optional[List["SkillTestResult"]] = None

# Cần khai báo update_forward_refs() nếu có tham chiếu vòng (ví dụ: CandidatePublic tham chiếu MatchResultPublic)
CandidatePublic.model_rebuild()

class CVJDUploadResponse(BaseModel): # Phản hồi sau khi tải CV/JD
    candidate_id: int
    message: str
    cv_text_extracted: bool
    jd_text_extracted: bool
    match_score: Optional[int] = None
    feedback: Optional[str] = None
    suggestions: Optional[List[str]] = None

# --- Schema cho so khớp (Matching) ---
class MatchResultPublic(BaseModel): # Dữ liệu kết quả so khớp khi hiển thị
    match_score: int
    feedback: str
    suggestions: List[str] # Sẽ được parse từ JSON string trong model thành list Python
    created_at: datetime

# --- Schema cho phỏng vấn (Interview) ---
class ChatbotMessage(BaseModel): # Tin nhắn từ người dùng gửi đến chatbot
    message: str

class ChatbotResponse(BaseModel): # Phản hồi từ chatbot
    response: str
    session_id: str
    first_message: Optional[str] = None # Cho tin nhắn khởi động phỏng vấn

class InterviewEvaluationRequest(BaseModel): # Yêu cầu đánh giá câu trả lời
    question: str
    candidate_answer: str
    jd_text: str

class InterviewEvaluationResponse(BaseModel): # Phản hồi đánh giá câu trả lời
    score: int
    feedback: str

# --- Schema cho kiểm tra kỹ năng (Skill Test) ---
class QuestionCreate(BaseModel): # Dữ liệu khi tạo câu hỏi mới
    question_text: str
    options: List[str]
    correct_answer: str
    skill_category: str

class QuestionPublic(BaseModel): # Dữ liệu câu hỏi khi hiển thị (không có đáp án đúng)
    id: int
    question_text: str
    options: List[str]
    skill_category: str

class AnswerSubmission(BaseModel): # Dữ liệu khi ứng viên nộp đáp án
    question_id: int
    selected_answer: str

class SkillTestStartResponse(BaseModel): # Phản hồi khi bắt đầu bài kiểm tra
    test_id: int
    questions: List[QuestionPublic]

class SkillTestSubmitResponse(BaseModel): # Phản hồi sau khi nộp bài kiểm tra
    test_result_id: int
    score: int
    total_questions: int

class SkillTestResultItemPublic(BaseModel): # Chi tiết từng câu trả lời trong kết quả
    question_text: str
    selected_answer: Optional[str]
    is_correct: Optional[bool]

class SkillTestResultPublic(BaseModel): # Kết quả bài kiểm tra đầy đủ
    id: int
    candidate_id: int
    score: Optional[int]
    total_questions: Optional[int]
    start_time: datetime
    end_time: Optional[datetime]
    items: List[SkillTestResultItemPublic]