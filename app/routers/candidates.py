from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status # Các công cụ FastAPI
from sqlmodel import Session, select # SQLModel để làm việc với DB
from sqlalchemy.orm import selectinload # Để tải các mối quan hệ (ví dụ: lấy ứng viên kèm theo kết quả phỏng vấn)
from typing import List, Optional # Kiểu dữ liệu Python
import json # Để xử lý JSON
from app.schemas.match_results_schemas import MatchResultPublic
from app.database import get_session # Lấy phiên DB
from app.models import Candidate, MatchResult, Interview, SkillTestResult # Các Model dữ liệu
from app.schemas import CandidateCreate, CandidatePublic, CVJDUploadResponse, MatchResultPublic, SendOfferRequest # Các Schemas
from app.services.cv_jd_processor import process_uploaded_file, get_cv_jd_matching_score_and_feedback, get_cv_improvement_suggestions # Dịch vụ xử lý CV/JD
from app.services.email_service import send_offer_email # Dịch vụ gửi email
from app.routers.auth import get_current_user # Dependency để bảo vệ các API (cần đăng nhập)

router = APIRouter()

@router.post("/", response_model=CandidatePublic, status_code=status.HTTP_201_CREATED)
async def create_candidate(
    candidate: CandidateCreate, # Dữ liệu ứng viên từ yêu cầu
    db: Session = Depends(get_session), # Phiên DB
    current_user: dict = Depends(get_current_user) # Yêu cầu người dùng đã đăng nhập
):
    """Tạo một hồ sơ ứng viên mới."""
    db_candidate = Candidate.model_validate(candidate) # Chuyển schema thành model DB
    db.add(db_candidate) # Thêm vào DB
    db.commit() # Lưu thay đổi
    db.refresh(db_candidate) # Cập nhật đối tượng Python với dữ liệu mới từ DB (ví dụ: ID)
    return db_candidate

@router.get("/", response_model=List[CandidatePublic])
async def read_candidates(
    offset: int = 0, # Bỏ qua bao nhiêu bản ghi
    limit: int = 100, # Giới hạn số bản ghi trả về
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Đọc danh sách các ứng viên."""
    candidates = db.exec(select(Candidate).offset(offset).limit(limit)).all() # Truy vấn DB
    return candidates

@router.get("/{candidate_id}", response_model=CandidatePublic)
async def read_candidate(
    candidate_id: int, # ID của ứng viên muốn đọc
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Đọc thông tin chi tiết của một ứng viên cùng với các kết quả liên quan."""
    candidate = db.exec(
        select(Candidate)
        .where(Candidate.id == candidate_id)
        .options( # Tải các mối quan hệ (MatchResult, Interview, SkillTestResult) cùng lúc
            selectinload(Candidate.match_results),
            selectinload(Candidate.interviews),
            selectinload(Candidate.skill_tests)
        )
    ).first() # Lấy bản ghi đầu tiên (hoặc None nếu không tìm thấy)
    
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy ứng viên.")
    
    # Chuyển đổi chuỗi JSON của suggestions thành List[str] để phù hợp với schema
    if candidate.match_results:
        for mr in candidate.match_results:
            mr.suggestions = json.loads(mr.suggestions) if mr.suggestions else []
            
    return candidate

@router.post("/upload-cv-jd", response_model=CVJDUploadResponse)
async def upload_cv_jd(
    full_name: str = Form(...), # Dữ liệu từ form
    email: str = Form(...),
    applied_position: str = Form(...),
    cv_file: UploadFile = File(...), # File CV được tải lên
    jd_file: UploadFile = File(...), # File JD được tải lên
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Tải lên CV và JD, sau đó xử lý và phân tích bằng AI."""
    cv_content = await cv_file.read() # Đọc nội dung file CV
    jd_content = await jd_file.read() # Đọc nội dung file JD

    cv_text = await process_uploaded_file(cv_content, cv_file.filename) # Trích xuất văn bản từ CV
    jd_text = await process_uploaded_file(jd_content, jd_file.filename) # Trích xuất văn bản từ JD

    if not cv_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể trích xuất văn bản từ file CV. Vui lòng kiểm tra định dạng (PDF/DOCX) hoặc nội dung.")
    if not jd_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Không thể trích xuất văn bản từ file JD. Vui lòng kiểm tra định dạng (PDF/DOCX) hoặc nội dung.")

    # Tìm ứng viên theo email hoặc tạo mới nếu chưa có
    candidate = db.exec(select(Candidate).where(Candidate.email == email)).first()
    if not candidate:
        candidate = Candidate(full_name=full_name, email=email, applied_position=applied_position)
    
    # Cập nhật thông tin CV và JD cho ứng viên
    candidate.cv_text = cv_text
    candidate.jd_text = jd_text
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    # Xử lý với GPT để lấy điểm phù hợp và gợi ý
    matching_result_dict = await get_cv_jd_matching_score_and_feedback(cv_text, jd_text)
    suggestions_dict = await get_cv_improvement_suggestions(cv_text, jd_text)

    # Lấy dữ liệu từ kết quả GPT
    match_score = matching_result_dict.get("score", 0)
    feedback = matching_result_dict.get("feedback", "Không có phản hồi từ AI.")
    suggestions_list = suggestions_dict.get("suggestions", [])
    
    # Lưu kết quả so khớp vào cơ sở dữ liệu
    new_match_result = MatchResult(
        candidate_id=candidate.id,
        match_score=match_score,
        feedback=feedback,
        suggestions=json.dumps(suggestions_list), # Lưu list gợi ý thành chuỗi JSON
        jd_id=None # Có thể liên kết với JD nếu bạn quản lý riêng bảng JD
    )
    db.add(new_match_result)
    db.commit()
    db.refresh(new_match_result)
    
    return CVJDUploadResponse(
        candidate_id=candidate.id,
        message="File đã được xử lý và phân tích thành công!",
        cv_text_extracted=bool(cv_text),
        jd_text_extracted=bool(jd_text),
        match_score=match_score,
        feedback=feedback,
        suggestions=suggestions_list # Trả về list cho frontend
    )

@router.post("/send-offer", status_code=status.HTTP_200_OK)
async def send_offer_to_candidate(
    request: SendOfferRequest, # Dữ liệu yêu cầu gửi thư mời
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Gửi thư mời làm việc đến ứng viên."""
    candidate = db.get(Candidate, request.candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy ứng viên.")
    
    # Kiểm tra email để đảm bảo gửi đúng người
    if candidate.email != request.recipient_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email người nhận không khớp với email ứng viên trong hệ thống.")

    success = await send_offer_email(
        candidate_email=request.recipient_email,
        candidate_name=request.candidate_name,
        position_name=request.position_name
    )
    if not success:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Không thể gửi thư mời. Vui lòng kiểm tra cấu hình email server.")
        
    return {"message": "Thư mời đã được gửi thành công!"}