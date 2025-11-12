from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from .models import UserType


class TeacherBase(BaseModel):
    name: str = Field(..., max_length=255)
    institution: str = Field(..., max_length=255)
    email: EmailStr


class TeacherCreate(TeacherBase):
    password: str = Field(..., min_length=6)


class TeacherOut(TeacherBase):
    id: int
    tag: str

    class Config:
        from_attributes = True


class StudentBase(BaseModel):
    name: str = Field(..., max_length=255)
    email: EmailStr


class StudentCreate(StudentBase):
    password: str = Field(..., min_length=6)


class StudentCreateWithTag(StudentCreate):
    teacher_tag: str = Field(..., max_length=32)


class StudentOut(StudentBase):
    id: int

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    user_type: UserType


class TokenResponse(BaseModel):
    token: str
    user_id: int
    user_type: UserType
    expires_at: datetime


class SessionInfo(BaseModel):
    token: str
    user_id: int
    user_type: UserType
    created_at: datetime
    expires_at: datetime

    class Config:
        from_attributes = True


class TeacherTagResponse(BaseModel):
    tag: str


class StudentTagAttachRequest(BaseModel):
    teacher_tag: str = Field(..., max_length=32)


class MessageResponse(BaseModel):
    message: str


class CurrentUser(BaseModel):
    id: int
    user_type: UserType


class QuestionFile(BaseModel):
    column: str
    url: str


class QuestionAlternative(BaseModel):
    letter: str
    text: str | None
    text_raw: str | None


class QuestionDetail(BaseModel):
    id: int
    titulo: str
    ano: int
    index: int
    disciplina: str | None
    linguagem: str | None
    contexto: str | None
    contexto_raw: str | None
    inducao: str | None
    inducao_raw: str | None
    alternativas: list[QuestionAlternative]
    files: dict[str, str]


class QuestionAnswerRequest(BaseModel):
    alternativa: str = Field(..., pattern="^[A-Ea-e]$")

    def normalized(self) -> str:
        return self.alternativa.upper()


class QuestionAnswerResult(BaseModel):
    resposta_id: int
    correta: bool
    alternativa_correta: str | None


class StudentSummary(BaseModel):
    id: int
    name: str
    email: EmailStr
    total_respostas: int
    total_corretas: int
    total_erradas: int


class StudentAnswerDetail(BaseModel):
    id: int
    question_id: int
    question_index: int
    question_year: int
    question_title: str
    alternativa_escolhida: str
    alternativa_correta: str | None
    correta: bool
    responded_at: datetime
