from secrets import randbelow

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_teacher
from ..models import Teacher
from ..schemas import MessageResponse, TeacherCreate, TeacherOut, TeacherTagResponse
from ..security import hash_password

router = APIRouter(prefix="/teachers", tags=["Professores"])


def _generate_unique_tag(db: Session) -> str:
    for _ in range(20):
        candidate = f"{randbelow(10**4):04d}"
        exists = db.query(Teacher.id).filter(Teacher.tag == candidate).first()
        if not exists:
            return candidate
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Não foi possível gerar tag única")


@router.post("", response_model=TeacherOut, status_code=status.HTTP_201_CREATED)
def create_teacher(payload: TeacherCreate, db: Session = Depends(get_db)) -> TeacherOut:
    already = db.query(Teacher.id).filter(Teacher.email == payload.email).first()
    if already:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado")

    teacher = Teacher(
        name=payload.name,
        institution=payload.institution,
        email=payload.email,
        password_hash=hash_password(payload.password),
        tag=_generate_unique_tag(db),
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return TeacherOut.model_validate(teacher)


@router.get("/me", response_model=TeacherOut)
def get_profile(teacher: Teacher = Depends(get_current_teacher)) -> TeacherOut:
    return TeacherOut.model_validate(teacher)


@router.get("/me/tag", response_model=TeacherTagResponse)
def get_my_tag(teacher: Teacher = Depends(get_current_teacher)) -> TeacherTagResponse:
    return TeacherTagResponse(tag=teacher.tag)


@router.delete("/me", response_model=MessageResponse)
def deactivate_teacher(teacher: Teacher = Depends(get_current_teacher), db: Session = Depends(get_db)) -> MessageResponse:
    teacher.is_active = False
    db.add(teacher)
    db.commit()
    return MessageResponse(message="Professor desativado com sucesso")
