from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_student
from ..models import Question, Respondida
from ..schemas import (
    QuestionAnswerRequest,
    QuestionAnswerResult,
    QuestionAlternative,
    QuestionDetail,
)

router = APIRouter(prefix="/questions", tags=["Questões"])

FILE_COLUMNS = [
    "aquivo1",
    "arquivo2",
    "arquivo3",
    "arquivo4",
    "arquivo5",
    "arquivo6",
    "arquivo7",
    "arquivo8",
    "arquivo9",
    "arquivo10",
]

ALTERNATIVE_COLUMNS = {
    "A": "alternativaA",
    "B": "alternativaB",
    "C": "alternativaC",
    "D": "altenartivaD",
    "E": "alternativaE",
}


def _collect_files(question: Question) -> dict[str, str]:
    files: dict[str, str] = {}
    for column in FILE_COLUMNS:
        value = getattr(question, column, None)
        if value:
            files[column] = value
    return files


def _render_text(text: str | None, files: dict[str, str]) -> str | None:
    if text is None:
        return None
    rendered = text
    for column, url in files.items():
        rendered = rendered.replace(f"{{{{{column}}}}}", url)
    return rendered


def _build_question_detail(question: Question) -> QuestionDetail:
    files = _collect_files(question)
    alternativas: list[QuestionAlternative] = []
    for letter, column in ALTERNATIVE_COLUMNS.items():
        text_raw = getattr(question, column, None)
        alternativas.append(
            QuestionAlternative(
                letter=letter,
                text_raw=text_raw,
                text=_render_text(text_raw, files),
            )
        )
    return QuestionDetail(
        id=question.id,
        titulo=question.titulo,
        ano=question.ano,
        index=question.index,
        disciplina=question.disciplina,
        linguagem=question.linguagem,
        contexto_raw=question.contexto,
        contexto=_render_text(question.contexto, files),
        inducao_raw=question.inducaoaalternativa,
        inducao=_render_text(question.inducaoaalternativa, files),
        alternativas=alternativas,
        files=files,
    )


@router.get("/random", response_model=QuestionDetail)
def get_random_question(
    student=Depends(get_current_student), db: Session = Depends(get_db)
) -> QuestionDetail:
    question = db.query(Question).order_by(func.random()).first()
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhuma questão disponível")
    return _build_question_detail(question)


@router.post("/{question_id}/answer", response_model=QuestionAnswerResult)
def answer_question(
    question_id: int,
    payload: QuestionAnswerRequest,
    student=Depends(get_current_student),
    db: Session = Depends(get_db),
) -> QuestionAnswerResult:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Questão não encontrada")

    alternativa = payload.normalized()
    if alternativa not in ALTERNATIVE_COLUMNS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Alternativa inválida")

    correta = question.alternativa_correta == alternativa

    resposta = Respondida(
        student_id=student.id,
        question_id=question.id,
        alternativa_escolhida=alternativa,
        correta=correta,
    )
    db.add(resposta)
    db.commit()
    db.refresh(resposta)

    return QuestionAnswerResult(
        resposta_id=resposta.id,
        correta=correta,
        alternativa_correta=question.alternativa_correta,
    )
