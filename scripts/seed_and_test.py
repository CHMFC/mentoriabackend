from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import Base, SessionLocal, engine
from app.main import app

ROOT = Path(__file__).resolve().parent


def reset_database() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        session.execute(text("TRUNCATE TABLE sessions RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE student_teacher_links RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE students RESTART IDENTITY CASCADE"))
        session.execute(text("TRUNCATE TABLE teachers RESTART IDENTITY CASCADE"))
        session.commit()


def run_flow() -> dict[str, object]:
    client = TestClient(app)

    teacher_payload = {
        "name": "Prof. Ada Lovelace",
        "institution": "Instituto Mentoria",
        "email": "ada.lovelace@example.com",
        "password": "senhaForte123",
    }
    teacher_resp = client.post("/teachers", json=teacher_payload)
    teacher_resp.raise_for_status()
    teacher_data = teacher_resp.json()

    login_teacher_resp = client.post(
        "/auth/login",
        json={
            "email": teacher_payload["email"],
            "password": teacher_payload["password"],
            "user_type": "teacher",
        },
    )
    login_teacher_resp.raise_for_status()
    teacher_session = login_teacher_resp.json()

    auth_header = {"Authorization": f"Bearer {teacher_session['token']}"}

    tag_resp = client.get("/teachers/me/tag", headers=auth_header)
    tag_resp.raise_for_status()
    teacher_tag = tag_resp.json()["tag"]

    student_payload = {
        "name": "Aluno Alan Turing",
        "email": "alan.turing@example.com",
        "password": "senhaAluno123",
    }
    student_resp = client.post("/students", headers=auth_header, json=student_payload)
    student_resp.raise_for_status()
    student_data = student_resp.json()

    student_self_payload = {
        "name": "Aluno Grace Hopper",
        "email": "grace.hopper@example.com",
        "password": "senhaAluno456",
        "teacher_tag": teacher_tag,
    }
    student_self_resp = client.post("/students/self-register", json=student_self_payload)
    student_self_resp.raise_for_status()
    student_self_data = student_self_resp.json()

    login_student_resp = client.post(
        "/auth/login",
        json={
            "email": student_self_payload["email"],
            "password": student_self_payload["password"],
            "user_type": "student",
        },
    )
    login_student_resp.raise_for_status()
    student_session = login_student_resp.json()

    student_headers = {"Authorization": f"Bearer {student_session['token']}"}
    profile_resp = client.get("/students/me", headers=student_headers)
    profile_resp.raise_for_status()

    second_teacher_payload = {
        "name": "Prof. Katherine Johnson",
        "institution": "Mentoria Avançada",
        "email": "katherine.johnson@example.com",
        "password": "senhaForte456",
    }
    second_teacher_resp = client.post("/teachers", json=second_teacher_payload)
    second_teacher_resp.raise_for_status()
    second_teacher_tag = second_teacher_resp.json()["tag"]

    attach_tag_resp = client.post(
        "/students/me/tags",
        headers=student_headers,
        json={"teacher_tag": second_teacher_tag},
    )
    attach_tag_resp.raise_for_status()

    session_info_resp = client.get("/auth/session", headers={"Authorization": f"Bearer {teacher_session['token']}"})
    session_info_resp.raise_for_status()

    return {
        "teacher": teacher_data,
        "teacher_session": teacher_session,
        "teacher_tag": teacher_tag,
        "student": student_data,
        "student_self": student_self_data,
        "student_session": student_session,
        "student_profile": profile_resp.json(),
        "second_teacher_tag": second_teacher_tag,
        "attach_tag_message": attach_tag_resp.json(),
        "session_info": session_info_resp.json(),
    }


def main() -> None:
    reset_database()
    results = run_flow()
    output_path = ROOT / "seed_and_test_output.json"
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Seed e testes executados com sucesso. Resultados salvos em {output_path}")


if __name__ == "__main__":
    main()
