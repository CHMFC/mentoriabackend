import enum
from datetime import datetime, timedelta
from secrets import token_urlsafe

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .config import settings
from .database import Base


class UserType(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"


student_teacher_association = Table(
    "student_teacher_links",
    Base.metadata,
    Column("student_id", ForeignKey("students.id", ondelete="CASCADE"), primary_key=True),
    Column("teacher_id", ForeignKey("teachers.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("student_id", "teacher_id", name="uq_student_teacher"),
)


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tag: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    students: Mapped[list["Student"]] = relationship(
        "Student", secondary=student_teacher_association, back_populates="teachers"
    )


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    teachers: Mapped[list[Teacher]] = relationship(
        "Teacher", secondary=student_teacher_association, back_populates="students"
    )


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    token: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    @classmethod
    def build(cls, user_id: int, user_type: UserType) -> "Session":
        token = token_urlsafe(32)
        expiration = datetime.utcnow() + timedelta(minutes=settings.access_token_ttl_minutes)
        return cls(token=token, user_id=user_id, user_type=user_type, expires_at=expiration)


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(512), nullable=False)
    index: Mapped[int] = mapped_column(Integer, nullable=False)
    ano: Mapped[int] = mapped_column(Integer, nullable=False)
    linguagem: Mapped[str | None] = mapped_column(String(64))
    disciplina: Mapped[str | None] = mapped_column(String(128))
    contexto: Mapped[str | None] = mapped_column(Text)
    aquivo1: Mapped[str | None] = mapped_column(String(512))
    arquivo2: Mapped[str | None] = mapped_column(String(512))
    arquivo3: Mapped[str | None] = mapped_column(String(512))
    arquivo4: Mapped[str | None] = mapped_column(String(512))
    arquivo5: Mapped[str | None] = mapped_column(String(512))
    arquivo6: Mapped[str | None] = mapped_column(String(512))
    arquivo7: Mapped[str | None] = mapped_column(String(512))
    arquivo8: Mapped[str | None] = mapped_column(String(512))
    arquivo9: Mapped[str | None] = mapped_column(String(512))
    arquivo10: Mapped[str | None] = mapped_column(String(512))
    alternativa_correta: Mapped[str | None] = mapped_column(String(1))
    inducaoaalternativa: Mapped[str | None] = mapped_column(Text)
    alternativaA: Mapped[str | None] = mapped_column(Text)
    alternativaB: Mapped[str | None] = mapped_column(Text)
    alternativaC: Mapped[str | None] = mapped_column(Text)
    altenartivaD: Mapped[str | None] = mapped_column(Text)
    alternativaE: Mapped[str | None] = mapped_column(Text)
