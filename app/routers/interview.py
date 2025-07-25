from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
import uuid # Để tạo ID duy nhất cho phiên trò chuyện
import json # Để xử lý JSON

from app.database import get_session
from app.models import Candidate, Interview
from app.schemas import ChatbotMessage, ChatbotResponse, InterviewEvaluationRequest, InterviewEvaluationResponse
from app.services.chatbot_service import start_interview, chat_with_chatbot, evaluate_candidate_response, store # Import 'store' để quản lý lịch sử
from app.routers.auth import get_current_user

router = APIRouter()

@router.post("/start/{candidate_id}", response_model=ChatbotResponse)
async def begin_interview(
    candidate_id: int, 
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Bắt đầu một phiên phỏng vấn AI mới cho ứng viên."""
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy ứng viên.")
    
    # Tạo một ID phiên ngẫu nhiên duy nhất
    session_id = str(uuid.uuid4())
    
    # Khởi tạo hoặc xóa lịch sử trò chuyện cho phiên này
    if session_id in store:
        store[session_id].clear()

    # Tạo một bản ghi phỏng vấn mới trong cơ sở dữ liệu
    new_interview = Interview(candidate_id=candidate_id, session_id=session_id)
    db.add(new_interview)
    db.commit()
    db.refresh(new_interview)

    # Lấy tin nhắn khởi tạo từ chatbot
    initial_message_text = await start_interview(session_id)

    return ChatbotResponse(response=initial_message_text, session_id=session_id, first_message=initial_message_text)

@router.post("/chat/{session_id}", response_model=ChatbotResponse)
async def continue_interview_chat(
    session_id: str, # ID phiên trò chuyện
    message: ChatbotMessage, # Tin nhắn từ người dùng
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Tiếp tục cuộc trò chuyện phỏng vấn AI."""
    interview_record = db.exec(select(Interview).where(Interview.session_id == session_id)).first()
    if not interview_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phiên phỏng vấn.")
    
    # Lấy phản hồi từ chatbot
    chatbot_response_text = await chat_with_chatbot(session_id, message.message)

    return ChatbotResponse(response=chatbot_response_text, session_id=session_id)

@router.post("/evaluate", response_model=InterviewEvaluationResponse)
async def evaluate_interview_response(
    request: InterviewEvaluationRequest, # Yêu cầu đánh giá
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Đánh giá một câu trả lời cụ thể của ứng viên trong buổi phỏng vấn."""
    # Lấy JD text của ứng viên để AI có ngữ cảnh đánh giá
    candidate = db.exec(select(Candidate).where(Candidate.id == request.candidate_id)).first() # Giả sử request có candidate_id
    jd_text = candidate.jd_text if candidate and candidate.jd_text else "" # Lấy JD từ ứng viên hoặc để trống nếu không có

    if not jd_text and not request.jd_text: # Nếu cả hai đều không có JD
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Văn bản JD là bắt buộc để đánh giá.")

    # Gọi dịch vụ AI để đánh giá
    evaluation_result = await evaluate_candidate_response(
        request.question, request.candidate_answer, jd_text if jd_text else request.jd_text
    )
    return InterviewEvaluationResponse(**evaluation_result) # Trả về kết quả đánh giá


@router.post("/end/{session_id}", status_code=status.HTTP_200_OK)
async def end_interview(
    session_id: str,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Kết thúc một phiên phỏng vấn AI."""
    interview_record = db.exec(select(Interview).where(Interview.session_id == session_id)).first()
    if not interview_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy phiên phỏng vấn.")
    
    if interview_record.end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Phỏng vấn đã kết thúc.")

    # Cập nhật thời gian kết thúc phỏng vấn trong DB
    interview_record.end_time = datetime.utcnow()
    db.add(interview_record)
    db.commit()
    db.refresh(interview_record)

    # Xóa lịch sử trò chuyện trong bộ nhớ để giải phóng tài nguyên
    if session_id in store:
        del store[session_id]

    return {"message": "Phỏng vấn đã kết thúc thành công."}