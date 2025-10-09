# models.py
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON, TIMESTAMP, func
from sqlalchemy.orm import relationship
#from .database import Base
import database  # absolute import

class Student(database.Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String)
    student_id = Column(String)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    assignments = relationship("Assignment", back_populates="student")


class Assignment(database.Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    filename = Column(String)
    original_text = Column(Text)
    topic = Column(String)
    academic_level = Column(String)
    word_count = Column(Integer)
    uploaded_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="assignments")
    analysis_result = relationship("AnalysisResult", back_populates="assignment", uselist=False)


class AnalysisResult(database.Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    suggested_sources = Column(JSON)
    plagiarism_score = Column(Float)
    flagged_sections = Column(JSON)
    research_suggestions = Column(Text)
    citation_recommendations = Column(Text)
    confidence_score = Column(Float)
    analyzed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    assignment = relationship("Assignment", back_populates="analysis_result")


class AcademicSource(database.Base):
    __tablename__ = "academic_sources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    authors = Column(String)
    publication_year = Column(Integer)
    abstract = Column(Text)
    full_text = Column(Text)
    source_type = Column(String)  # e.g., 'paper', 'textbook', 'course_material'
    embedding = Column(Text)  # for pgvector use later
