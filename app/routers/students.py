from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_student, get_current_teacher
from ..models import Student, Teacher
from ..schemas import (
    MessageResponse,
    StudentCreate,
    StudentCreateWithTag,
    StudentOut,
    StudentTagAttachRequest,
)
from ..security import hash_password

router = APIRouter(prefix="/students", tags=["Alunos"])


def _ensure_unique_email(db: Session, email: str) -> None:
    exists = db.query(Student.id).filter(Student.email == email).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email de aluno já cadastrado")


@router.post("/self-register", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def student_self_register(payload: StudentCreateWithTag, db: Session = Depends(get_db)) -> StudentOut:
    teacher = db.query(Teacher).filter(Teacher.tag == payload.teacher_tag, Teacher.is_active.is_(True)).first()
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor com esta tag não encontrado")

    _ensure_unique_email(db, payload.email)

    student = Student(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    student.teachers.append(teacher)

    db.add(student)
    db.commit()
    db.refresh(student)

    return StudentOut.model_validate(student)


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student_for_teacher(
    payload: StudentCreate,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
) -> StudentOut:
    _ensure_unique_email(db, payload.email)

    student = Student(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    student.teachers.append(teacher)

    db.add(student)
    db.commit()
    db.refresh(student)

    return StudentOut.model_validate(student)


@router.post("/me/tags", response_model=MessageResponse)
def add_teacher_tag(
    payload: StudentTagAttachRequest,
    student: Student = Depends(get_current_student),
    db: Session = Depends(get_db),
) -> MessageResponse:
    teacher = db.query(Teacher).filter(Teacher.tag == payload.teacher_tag, Teacher.is_active.is_(True)).first()
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Professor com esta tag não encontrado")

    if teacher in student.teachers:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tag já vinculada a este aluno")

    student.teachers.append(teacher)
    db.add(student)
    db.commit()

    return MessageResponse(message="Tag de professor adicionada com sucesso")


@router.get("/me", response_model=StudentOut)
def get_profile(student: Student = Depends(get_current_student)) -> StudentOut:
    return StudentOut.model_validate(student)
