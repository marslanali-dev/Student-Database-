from sqlalchemy import (
    Column, Integer, String, Float, Boolean, Date, DateTime,
    ForeignKey, Enum, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database.db import Base


# ─── Enums ────────────────────────────────────────────────────────────────────

class RoleEnum(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"
    parent = "parent"


class GradeEnum(str, enum.Enum):
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C_PLUS = "C+"
    C = "C"
    D = "D"
    F = "F"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"
    excused = "excused"


class FeeStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"
    waived = "waived"


class AssignmentStatus(str, enum.Enum):
    pending = "pending"
    submitted = "submitted"
    graded = "graded"
    late = "late"


class SalaryStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    partial = "partial"


# ─── User (Auth) ───────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.student)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    student_profile = relationship("Student", back_populates="user", uselist=False)
    teacher_profile = relationship("Teacher", back_populates="user", uselist=False)


# ─── Class / Section ──────────────────────────────────────────────────────────

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)          # e.g., "Grade 10"
    section = Column(String(10), nullable=False)        # e.g., "A"
    academic_year = Column(String(10), nullable=False)  # e.g., "2024-25"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("name", "section", "academic_year"),)

    students = relationship("Student", back_populates="class_")
    subjects = relationship("Subject", back_populates="class_")


# ─── Subject ──────────────────────────────────────────────────────────────────

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    total_marks = Column(Integer, default=100)
    passing_marks = Column(Integer, default=40)
    credit_hours = Column(Integer, default=3)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    class_ = relationship("Class", back_populates="subjects")
    teacher = relationship("Teacher", back_populates="subjects")
    results = relationship("Result", back_populates="subject")
    assignments = relationship("Assignment", back_populates="subject")
    attendances = relationship("Attendance", back_populates="subject")


# ─── Student ──────────────────────────────────────────────────────────────────

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    roll_number = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    parent_name = Column(String(100), nullable=True)
    parent_phone = Column(String(20), nullable=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    admission_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="student_profile")
    class_ = relationship("Class", back_populates="students")
    results = relationship("Result", back_populates="student")
    attendances = relationship("Attendance", back_populates="student")
    fees = relationship("Fee", back_populates="student")
    assignment_submissions = relationship("AssignmentSubmission", back_populates="student")


# ─── Teacher ──────────────────────────────────────────────────────────────────

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    employee_id = Column(String(20), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    qualification = Column(String(100), nullable=True)
    specialization = Column(String(100), nullable=True)
    joining_date = Column(Date, nullable=True)
    base_salary = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="teacher_profile")
    subjects = relationship("Subject", back_populates="teacher")
    salaries = relationship("Salary", back_populates="teacher")


# ─── Result (Report Card) ─────────────────────────────────────────────────────

class Result(Base):
    __tablename__ = "results"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    exam_type = Column(String(50), nullable=False)   # midterm / final / quiz
    marks_obtained = Column(Float, nullable=False)
    total_marks = Column(Float, nullable=False)
    grade = Column(Enum(GradeEnum), nullable=True)
    remarks = Column(Text, nullable=True)
    exam_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("student_id", "subject_id", "exam_type"),)

    student = relationship("Student", back_populates="results")
    subject = relationship("Subject", back_populates="results")


# ─── Attendance ───────────────────────────────────────────────────────────────

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.present)
    remarks = Column(String(200), nullable=True)
    marked_by = Column(Integer, ForeignKey("teachers.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("student_id", "subject_id", "date"),)

    student = relationship("Student", back_populates="attendances")
    subject = relationship("Subject", back_populates="attendances")


# ─── Fee ──────────────────────────────────────────────────────────────────────

class Fee(Base):
    __tablename__ = "fees"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    fee_type = Column(String(50), nullable=False)      # tuition / exam / library etc.
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    paid_date = Column(Date, nullable=True)
    paid_amount = Column(Float, default=0.0)
    status = Column(Enum(FeeStatus), default=FeeStatus.pending)
    month = Column(String(20), nullable=True)           # e.g., "January 2025"
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    student = relationship("Student", back_populates="fees")


# ─── Assignment ───────────────────────────────────────────────────────────────

class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    total_marks = Column(Float, default=10.0)
    due_date = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    subject = relationship("Subject", back_populates="assignments")
    submissions = relationship("AssignmentSubmission", back_populates="assignment")


class AssignmentSubmission(Base):
    __tablename__ = "assignment_submissions"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    submission_text = Column(Text, nullable=True)
    file_url = Column(String(500), nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    marks_obtained = Column(Float, nullable=True)
    status = Column(Enum(AssignmentStatus), default=AssignmentStatus.submitted)
    feedback = Column(Text, nullable=True)

    __table_args__ = (UniqueConstraint("assignment_id", "student_id"),)

    assignment = relationship("Assignment", back_populates="submissions")
    student = relationship("Student", back_populates="assignment_submissions")


# ─── Salary ───────────────────────────────────────────────────────────────────

class Salary(Base):
    __tablename__ = "salaries"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    month = Column(String(20), nullable=False)          # e.g., "January 2025"
    base_salary = Column(Float, nullable=False)
    allowances = Column(Float, default=0.0)
    deductions = Column(Float, default=0.0)
    net_salary = Column(Float, nullable=False)
    paid_date = Column(Date, nullable=True)
    status = Column(Enum(SalaryStatus), default=SalaryStatus.pending)
    remarks = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (UniqueConstraint("teacher_id", "month"),)

    teacher = relationship("Teacher", back_populates="salaries")
