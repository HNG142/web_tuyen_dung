from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List
import json 
from datetime import datetime 

from app.database import get_session
from app.models import Question, SkillTestResult, SkillTestResultItem, Candidate # Các Model
from app.schemas import QuestionCreate, QuestionPublic, AnswerSubmission, SkillTestStartResponse, SkillTestSubmitResponse, SkillTestResultPublic, SkillTestResultItemPublic # Các Schemas
from app.routers.auth import get_current_user # Dependency xác thực

router = APIRouter()

@router.post("/questions/", response_model=QuestionPublic, status_code=status.HTTP_201_CREATED)
async def create_question(
    question: QuestionCreate, 
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Tạo một câu hỏi trắc nghiệm mới."""
    # Chuyển đổi list options thành chuỗi JSON để lưu vào DB
    db_question = Question(
        question_text=question.question_text,
        options=json.dumps(question.options), 
        correct_answer=question.correct_answer,
        skill_category=question.skill_category
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    # Chuyển đổi lại options thành list cho phản hồi API
    db_question.options = json.loads(db_question.options)
    return db_question

@router.get("/questions/{skill_category}", response_model=List[QuestionPublic])
async def get_questions_by_category(
    skill_category: str, 
    limit: int = 10, # Giới hạn số câu hỏi
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Lấy danh sách câu hỏi theo danh mục kỹ năng."""
    questions = db.exec(
        select(Question).where(Question.skill_category == skill_category).limit(limit)
    ).all()
    # Chuyển đổi options từ chuỗi JSON thành list cho mỗi câu hỏi
    for q in questions:
        q.options = json.loads(q.options)
    return questions

@router.post("/start/{candidate_id}/{skill_category}", response_model=SkillTestStartResponse)
async def start_skill_test(
    candidate_id: int, 
    skill_category: str, 
    limit: int = 10, 
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Bắt đầu một bài kiểm tra kỹ năng cho ứng viên."""
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy ứng viên.")

    # Lấy các câu hỏi cho bài kiểm tra
    questions = db.exec(
        select(Question).where(Question.skill_category == skill_category).limit(limit)
    ).all()
    
    if not questions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy câu hỏi nào cho danh mục '{skill_category}'.")

    # Tạo một bản ghi bài kiểm tra mới trong DB
    new_test_result = SkillTestResult(
        candidate_id=candidate_id,
        total_questions=len(questions)
    )
    db.add(new_test_result)
    db.commit()
    db.refresh(new_test_result)

    # Chuyển đổi các câu hỏi sang định dạng công khai (không có đáp án đúng)
    public_questions = [
        QuestionPublic(
            id=q.id,
            question_text=q.question_text,
            options=json.loads(q.options), # Chuyển đổi options từ chuỗi JSON
            skill_category=q.skill_category
        ) for q in questions
    ]

    return SkillTestStartResponse(test_id=new_test_result.id, questions=public_questions)


@router.post("/submit/{test_id}", response_model=SkillTestSubmitResponse)
async def submit_skill_test(
    test_id: int, # ID của bài kiểm tra
    answers: List[AnswerSubmission], # Danh sách các câu trả lời của ứng viên
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Nộp bài kiểm tra kỹ năng và tính điểm."""
    test_result = db.get(SkillTestResult, test_id)
    if not test_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy bài kiểm tra.")
    
    if test_result.end_time: # Kiểm tra nếu bài kiểm tra đã được nộp rồi
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bài kiểm tra đã được nộp rồi.")

    score = 0
    for submitted_answer in answers:
        question = db.get(Question, submitted_answer.question_id) # Lấy câu hỏi từ DB
        if question:
            is_correct = (submitted_answer.selected_answer == question.correct_answer)
            if is_correct:
                score += 1
            
            # Lưu chi tiết câu trả lời của ứng viên
            test_result_item = SkillTestResultItem(
                test_result_id=test_id,
                question_id=question.id,
                selected_answer=submitted_answer.selected_answer,
                is_correct=is_correct
            )
            db.add(test_result_item)
    
    # Cập nhật điểm và thời gian kết thúc bài kiểm tra
    test_result.score = score
    test_result.end_time = datetime.utcnow()
    db.add(test_result)
    db.commit()
    db.refresh(test_result)

    return SkillTestSubmitResponse(
        test_result_id=test_result.id,
        score=test_result.score,
        total_questions=test_result.total_questions
    )

@router.get("/results/{test_id}", response_model=SkillTestResultPublic)
async def get_test_results(
    test_id: int, 
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """Lấy chi tiết kết quả của một bài kiểm tra kỹ năng."""
    test_result = db.exec(
        select(SkillTestResult).where(SkillTestResult.id == test_id)
        .options(selectinload(SkillTestResult.items).options(selectinload(SkillTestResultItem.question))) # Tải các item và câu hỏi liên quan
    ).first()

    if not test_result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy kết quả bài kiểm tra.")

    # Chuẩn bị dữ liệu chi tiết câu trả lời cho phản hồi API
    items_public = []
    for item in test_result.items:
        items_public.append(
            SkillTestResultItemPublic(
                question_text=item.question.question_text if item.question else "N/A",
                selected_answer=item.selected_answer,
                is_correct=item.is_correct
            )
        )
    
    return SkillTestResultPublic(
        id=test_result.id,
        candidate_id=test_result.candidate_id,
        score=test_result.score,
        total_questions=test_result.total_questions,
        start_time=test_result.start_time,
        end_time=test_result.end_time,
        items=items_public
    )