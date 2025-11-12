from secrets import randbelow

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Integer, cast, func
from sqlalchemy.orm import Session, joinedload

from ..database import get_db
from ..deps import get_current_teacher
from ..models import Respondida, Teacher, student_teacher_association, Student
from ..schemas import (
    MessageResponse,
    StudentAnswerDetail,
    StudentSummary,
    TeacherCreate,
    TeacherOut,
    TeacherTagResponse,
)
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


@router.get("/me/students", response_model=list[StudentSummary])
def list_students(teacher: Teacher = Depends(get_current_teacher), db: Session = Depends(get_db)) -> list[StudentSummary]:
    stats = (
        db.query(
            Student.id,
            Student.name,
            Student.email,
            func.count(Respondida.id).label("total"),
            func.coalesce(func.sum(cast(Respondida.correta, Integer)), 0).label("corretas"),
        )
        .join(
            student_teacher_association,
            Student.id == student_teacher_association.c.student_id,
        )
        .filter(
            student_teacher_association.c.teacher_id == teacher.id,
            Student.is_active.is_(True),
        )
        .outerjoin(Respondida, Respondida.student_id == Student.id)
        .group_by(Student.id, Student.name, Student.email)
        .order_by(Student.name)
        .all()
    )

    summaries: list[StudentSummary] = []
    for student_id, name, email, total, corretas in stats:
        total_int = int(total)
        corretas_int = int(corretas) if corretas is not None else 0
        erradas = total_int - corretas_int
        summaries.append(
            StudentSummary(
                id=student_id,
                name=name,
                email=email,
                total_respostas=total_int,
                total_corretas=corretas_int,
                total_erradas=erradas,
            )
        )
    return summaries


@router.get("/students/{student_id}/answers", response_model=list[StudentAnswerDetail])
def get_student_answers(
    student_id: int,
    teacher: Teacher = Depends(get_current_teacher),
    db: Session = Depends(get_db),
) -> list[StudentAnswerDetail]:
    association = (
        db.query(student_teacher_association)
        .filter(
            student_teacher_association.c.teacher_id == teacher.id,
            student_teacher_association.c.student_id == student_id,
        )
        .first()
    )
    if association is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aluno não encontrado para este professor",
        )

    respostas = (
        db.query(Respondida)
        .options(joinedload(Respondida.question))
        .filter(Respondida.student_id == student_id)
        .order_by(Respondida.created_at.desc())
        .all()
    )

    details: list[StudentAnswerDetail] = []
    for resposta in respostas:
        question = resposta.question
        details.append(
            StudentAnswerDetail(
                id=resposta.id,
                question_id=resposta.question_id,
                question_index=question.index if question else 0,
                question_year=question.ano if question else 0,
                question_title=question.titulo if question else "Questão removida",
                alternativa_escolhida=resposta.alternativa_escolhida,
                alternativa_correta=question.alternativa_correta if question else None,
                correta=resposta.correta,
                responded_at=resposta.created_at,
            )
        )
    return details
