from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import Question

PUBLIC_DIR = Path(__file__).resolve().parents[1] / "public"
SUPPORTED_FILE_COLUMNS = [
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


@dataclass
class QuestionPayload:
    titulo: str
    index: int
    ano: int
    linguagem: str | None
    disciplina: str | None
    contexto: str | None
    inducao: str | None
    alternativa_correta: str | None
    alternativas: dict[str, str | None]
    arquivos: dict[str, str | None]
    overflow_count: int


def _load_details(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _assign_files(files: list[str]) -> dict[str, str | None]:
    columns: dict[str, str | None] = {name: None for name in SUPPORTED_FILE_COLUMNS}
    for idx, file_url in enumerate(files):
        if idx >= len(SUPPORTED_FILE_COLUMNS):
            break
        columns[SUPPORTED_FILE_COLUMNS[idx]] = file_url
    return columns


def _replace_file_references(text: str | None, mapping: dict[str, str]) -> str | None:
    if text is None:
        return None
    new_text = text
    for url, column in mapping.items():
        placeholder = f"{{{{{column}}}}}"
        new_text = new_text.replace(url, placeholder)
    return new_text


def _extract_question_payload(path: Path) -> QuestionPayload:
    data = _load_details(path)
    collected_files: list[str] = []
    for file_url in data.get("files") or []:
        if file_url and file_url not in collected_files:
            collected_files.append(file_url)

    alternatives_raw = data.get("alternatives") or []
    alternativas: dict[str, str | None] = {}
    file_references: dict[str, str] = {}

    for alt in alternatives_raw:
        letter = alt.get("letter")
        alt_text = alt.get("text")
        alt_file = alt.get("file")
        if alt_file and alt_file not in collected_files:
            collected_files.append(alt_file)
        alternativas[letter] = alt_text

    arquivo_mapping = _assign_files(collected_files)

    for column, url in arquivo_mapping.items():
        if url:
            file_references[url] = column

    contexto = _replace_file_references(data.get("context"), file_references)
    inducao = _replace_file_references(data.get("alternativesIntroduction"), file_references)

    alternativas_transformadas: dict[str, str | None] = {}
    for letter, alt_text in alternativas.items():
        alternativas_transformadas[letter] = _replace_file_references(alt_text, file_references)

    overflow = max(0, len(collected_files) - len(SUPPORTED_FILE_COLUMNS))

    return QuestionPayload(
        titulo=data.get("title") or f"Questão {data.get('index')}",
        index=int(data.get("index")),
        ano=int(data.get("year")),
        linguagem=data.get("language"),
        disciplina=data.get("discipline"),
        contexto=contexto,
        inducao=inducao,
        alternativa_correta=data.get("correctAlternative"),
        alternativas=alternativas_transformadas,
        arquivos=arquivo_mapping,
        overflow_count=overflow,
    )


def _iter_detail_files() -> Iterator[Path]:
    if not PUBLIC_DIR.exists():
        raise FileNotFoundError(f"Pasta 'public' não encontrada em {PUBLIC_DIR}")
    for year_dir in sorted(PUBLIC_DIR.iterdir()):
        if not year_dir.is_dir():
            continue
        questions_dir = year_dir / "questions"
        if not questions_dir.exists():
            continue
        for detail_path in sorted(questions_dir.glob("*/details.json")):
            yield detail_path


def upsert_question(session: Session, payload: QuestionPayload) -> None:
    stmt = select(Question).where(Question.ano == payload.ano, Question.index == payload.index)
    result = session.execute(stmt).scalar_one_or_none()

    arquivos = payload.arquivos
    alternativas = payload.alternativas

    if result is None:
        question = Question(
            titulo=payload.titulo,
            index=payload.index,
            ano=payload.ano,
            linguagem=payload.linguagem,
            disciplina=payload.disciplina,
            contexto=payload.contexto,
            aquivo1=arquivos["aquivo1"],
            arquivo2=arquivos["arquivo2"],
            arquivo3=arquivos["arquivo3"],
            arquivo4=arquivos["arquivo4"],
            arquivo5=arquivos["arquivo5"],
            arquivo6=arquivos["arquivo6"],
            arquivo7=arquivos["arquivo7"],
            arquivo8=arquivos["arquivo8"],
            arquivo9=arquivos["arquivo9"],
            arquivo10=arquivos["arquivo10"],
            alternativa_correta=payload.alternativa_correta,
            inducaoaalternativa=payload.inducao,
            alternativaA=alternativas.get("A"),
            alternativaB=alternativas.get("B"),
            alternativaC=alternativas.get("C"),
            altenartivaD=alternativas.get("D"),
            alternativaE=alternativas.get("E"),
        )
        session.add(question)
    else:
        result.titulo = payload.titulo
        result.index = payload.index
        result.ano = payload.ano
        result.linguagem = payload.linguagem
        result.disciplina = payload.disciplina
        result.contexto = payload.contexto
        result.aquivo1 = arquivos["aquivo1"]
        result.arquivo2 = arquivos["arquivo2"]
        result.arquivo3 = arquivos["arquivo3"]
        result.arquivo4 = arquivos["arquivo4"]
        result.arquivo5 = arquivos["arquivo5"]
        result.arquivo6 = arquivos["arquivo6"]
        result.arquivo7 = arquivos["arquivo7"]
        result.arquivo8 = arquivos["arquivo8"]
        result.arquivo9 = arquivos["arquivo9"]
        result.arquivo10 = arquivos["arquivo10"]
        result.alternativa_correta = payload.alternativa_correta
        result.inducaoaalternativa = payload.inducao
        result.alternativaA = alternativas.get("A")
        result.alternativaB = alternativas.get("B")
        result.alternativaC = alternativas.get("C")
        result.altenartivaD = alternativas.get("D")
        result.alternativaE = alternativas.get("E")


def main() -> None:
    Base.metadata.create_all(bind=engine)

    processed = 0
    skipped_overflow = 0

    with SessionLocal() as session:
        for detail_path in _iter_detail_files():
            payload = _extract_question_payload(detail_path)
            if payload.overflow_count > 0:
                skipped_overflow += 1
            upsert_question(session, payload)
            processed += 1
        session.commit()

    print(
        f"Importação concluída. Questões processadas: {processed}. "
        f"Registros com mais de {len(SUPPORTED_FILE_COLUMNS)} arquivos: {skipped_overflow}."
    )


if __name__ == "__main__":
    main()

