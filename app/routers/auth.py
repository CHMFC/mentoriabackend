from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Session as SessionModel
from ..models import Student, Teacher, UserType
from ..schemas import LoginRequest, SessionInfo, TokenResponse
from ..security import verify_password
from ..deps import get_current_session

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if payload.user_type == UserType.TEACHER:
        user = db.query(Teacher).filter(Teacher.email == payload.email, Teacher.is_active.is_(True)).first()
    else:
        user = db.query(Student).filter(Student.email == payload.email, Student.is_active.is_(True)).first()

    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    session = SessionModel.build(user_id=user.id, user_type=payload.user_type)
    db.add(session)
    db.commit()
    db.refresh(session)

    return TokenResponse(
        token=session.token,
        user_id=session.user_id,
        user_type=session.user_type,
        expires_at=session.expires_at,
    )


@router.get("/session", response_model=SessionInfo)
def get_session_info(session: SessionModel = Depends(get_current_session)) -> SessionInfo:
    return SessionInfo.model_validate(session)
