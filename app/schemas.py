from __future__ import annotations
from sqlmodel import Field, SQLModel, Relationship, Session, select
from app.models import MatchResultPublic
from pydantic import BaseModel, EmailStr 
from typing import List, Optional, Dict 
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserPublic(BaseModel): 
    id: int
    email: EmailStr
    is_active: bool
    is_admin: bool

class Token(BaseModel): 
    access_token: str
    token_type: str

class TokenData(BaseModel): 
    email: Optional[str] = None

class CandidateCreate(SQLModel): 
    full_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    applied_position: Optional[str] = None

class CandidatePublic(BaseModel): 
    id: int
    full_name: str
    email: str 
    match_results: List[MatchResultPublic]
  
    match_results: Optional[List["MatchResultPublic"]] = None
    interviews: Optional[List["Interview"]] = None
    skill_tests: Optional[List["SkillTestResult"]] = None

CandidatePublic.model_rebuild()

class CVJDUploadResponse(BaseModel): 
    candidate_id: int
    message: str
    cv_text_extracted: bool
    jd_text_extracted: bool
    match_score: Optional[int] = None
    feedback: Optional[str] = None
    suggestions: Optional[List[str]] = None

class MatchResultPublic(BaseModel): 
    match_score: int
    feedback: str
    suggestions: List[str] 
    created_at: datetime

class ChatbotMessage(BaseModel): 
    message: str

class ChatbotResponse(BaseModel): 
    response: str
    session_id: str
    first_message: Optional[str] = None 

class InterviewEvaluationRequest(BaseModel): 
    question: str
    candidate_answer: str
    jd_text: str

class InterviewEvaluationResponse(BaseModel): 
    score: int
    feedback: str

class QuestionCreate(BaseModel): 
    question_text: str
    options: List[str]
    correct_answer: str
    skill_category: str

class QuestionPublic(BaseModel): 
    id: int
    question_text: str
    options: List[str]
    skill_category: str

class AnswerSubmission(BaseModel): 
    question_id: int
    selected_answer: str

class SkillTestStartResponse(BaseModel): 
    test_id: int
    questions: List[QuestionPublic]

class SkillTestSubmitResponse(BaseModel): 
    test_result_id: int
    score: int
    total_questions: int

class SkillTestResultItemPublic(BaseModel): 
    question_text: str
    selected_answer: Optional[str]
    is_correct: Optional[bool]

class SkillTestResultPublic(BaseModel): 
    id: int
    candidate_id: int
    score: Optional[int]
    total_questions: Optional[int]
    start_time: datetime
    end_time: Optional[datetime]
    items: List[SkillTestResultItemPublic]