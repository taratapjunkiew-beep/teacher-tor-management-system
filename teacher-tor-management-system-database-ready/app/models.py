from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, Text, ForeignKey
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    username = __import__("sqlalchemy").Column(String(80), unique=True, index=True)
    full_name = __import__("sqlalchemy").Column(String(200), default="")
    password_hash = __import__("sqlalchemy").Column(String(255))
    role = __import__("sqlalchemy").Column(String(20), default="teacher")
    is_active = __import__("sqlalchemy").Column(Boolean, default=True)
    created_at = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)

class Course(Base):
    __tablename__ = "courses"

    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    code = __import__("sqlalchemy").Column(String(40), unique=True, index=True)
    name = __import__("sqlalchemy").Column(String(255), index=True)
    level = __import__("sqlalchemy").Column(String(100), default="ปวช.")
    curriculum = __import__("sqlalchemy").Column(String(255), default="หลักสูตรประกาศนียบัตรวิชาชีพ พุทธศักราช 2567")
    program_type = __import__("sqlalchemy").Column(String(255), default="")
    occupational_group = __import__("sqlalchemy").Column(String(255), default="")
    major = __import__("sqlalchemy").Column(String(255), default="")
    theory_hours = __import__("sqlalchemy").Column(Integer, default=1)
    practice_hours = __import__("sqlalchemy").Column(Integer, default=3)
    credits = __import__("sqlalchemy").Column(Integer, default=2)
    standard_ref = __import__("sqlalchemy").Column(Text, default="")
    learning_outcome = __import__("sqlalchemy").Column(Text, default="")
    objectives = __import__("sqlalchemy").Column(Text, default="[]")
    competencies = __import__("sqlalchemy").Column(Text, default="[]")
    description = __import__("sqlalchemy").Column(Text, default="")
    occupational_standard = __import__("sqlalchemy").Column(Text, default="")
    units = __import__("sqlalchemy").Column(Text, default="[]")
    assessment = __import__("sqlalchemy").Column(Text, default="")
    source_note = __import__("sqlalchemy").Column(Text, default="")
    is_verified = __import__("sqlalchemy").Column(Boolean, default=False)
    is_active = __import__("sqlalchemy").Column(Boolean, default=True)
    created_at = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)

class CurriculumFile(Base):
    __tablename__ = "curriculum_files"

    id = __import__("sqlalchemy").Column(Integer, primary_key=True, index=True)
    filename = __import__("sqlalchemy").Column(String(255))
    saved_path = __import__("sqlalchemy").Column(String(500))
    level_hint = __import__("sqlalchemy").Column(String(100), default="")
    major_hint = __import__("sqlalchemy").Column(String(255), default="")
    uploaded_by_id = __import__("sqlalchemy").Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = __import__("sqlalchemy").Column(DateTime, default=datetime.utcnow)
