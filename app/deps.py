from datetime import datetime

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import Session as SessionModel
from .models import Student, Teacher, UserType
from .schemas import CurrentUser

http_bearer = HTTPBearer(auto_error=False)


def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Security(http_bearer),
    db: Session = Depends(get_db),
) -> SessionModel:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")

    token = credentials.credentials
    session = (
        db.query(SessionModel)
        .filter(SessionModel.token == token)
        .order_by(SessionModel.created_at.desc())
        .first()
    )
    if session is None or session.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")
    return session


def get_current_user(session: SessionModel = Depends(get_current_session)) -> CurrentUser:
    return CurrentUser(id=session.user_id, user_type=session.user_type)


def get_current_teacher(
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
) -> Teacher:
    if current_user.user_type != UserType.TEACHER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a professores")

    teacher = db.query(Teacher).filter(Teacher.id == current_user.id, Teacher.is_active.is_(True)).first()
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor não encontrado")
    return teacher


def get_current_student(
    current_user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)
) -> Student:
    if current_user.user_type != UserType.STUDENT:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a estudantes")

    student = db.query(Student).filter(Student.id == current_user.id, Student.is_active.is_(True)).first()
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aluno não encontrado")
    return student
