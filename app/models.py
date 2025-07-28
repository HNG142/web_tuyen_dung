from __future__ import annotations
from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_admin: bool = Field(default=False)

    candidates: List["Candidate"] = Relationship(back_populates="user")

class Candidate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="candidates")

    full_name: str
    email: str = Field(unique=True, index=True)
    phone_number: Optional[str] = None
    applied_position: Optional[str] = None
    cv_text: Optional[str] = None
    jd_text: Optional[str] = None

    interviews: List["Interview"] = Relationship(back_populates="candidate")
    skill_tests: List["SkillTestResult"] = Relationship(back_populates="candidate")
    match_results: List["MatchResult"] = Relationship(back_populates="candidate")

class MatchResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id")
    candidate: Optional[Candidate] = Relationship(back_populates="match_results")

    jd_id: Optional[int] = None
    match_score: int
    feedback: str
    suggestions: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Interview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id")
    candidate: Optional[Candidate] = Relationship(back_populates="interviews")

    session_id: str = Field(unique=True, index=True)
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    overall_score: Optional[int] = None
    overall_feedback: Optional[str] = None

class Question(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    question_text: str
    options: str
    correct_answer: str
    skill_category: str

    test_results: List["SkillTestResultItem"] = Relationship(back_populates="question")

class SkillTestResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    candidate_id: int = Field(foreign_key="candidate.id")
    candidate: Optional[Candidate] = Relationship(back_populates="skill_tests")

    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    score: Optional[int] = None
    total_questions: Optional[int] = None

    items: List["SkillTestResultItem"] = Relationship(back_populates="test_result")

class SkillTestResultItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    test_result_id: int = Field(foreign_key="skilltestresult.id")
    test_result: Optional[SkillTestResult] = Relationship(back_populates="items")

    question_id: int = Field(foreign_key="question.id")
    question: Optional[Question] = Relationship(back_populates="test_results")

    selected_answer: Optional[str]
    is_correct: Optional[bool]

class MatchResultBase(SQLModel):
    match_score: int
    feedback: str
    suggestions: str
    created_at: datetime

class MatchResultCreate(MatchResultBase):
    pass

class MatchResultPublic(MatchResultBase):
    id: int

class User(BaseModel):
    email: str


user = User(email="test@example.com")
print(user.email)