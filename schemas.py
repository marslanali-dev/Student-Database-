from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import date, datetime
from models.models import (
    RoleEnum, GradeEnum, AttendanceStatus,
    FeeStatus, AssignmentStatus, SalaryStatus
)


# ─── Auth Schemas ─────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: RoleEnum = RoleEnum.student


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: RoleEnum
    is_active: bool
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class ChangePassword(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


# ─── Class Schemas ────────────────────────────────────────────────────────────

class ClassCreate(BaseModel):
    name: str = Field(..., example="Grade 10")
    section: str = Field(..., example="A")
    academic_year: str = Field(..., example="2024-25")


class ClassOut(BaseModel):
    id: int
    name: str
    section: str
    academic_year: str
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Subject Schemas ──────────────────────────────────────────────────────────

class SubjectCreate(BaseModel):
    name: str
    code: str
    class_id: int
    teacher_id: Optional[int] = None
    total_marks: int = 100
    passing_marks: int = 40
    credit_hours: int = 3
    description: Optional[str] = None


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    teacher_id: Optional[int] = None
    total_marks: Optional[int] = None
    passing_marks: Optional[int] = None
    credit_hours: Optional[int] = None
    description: Optional[str] = None


class SubjectOut(BaseModel):
    id: int
    name: str
    code: str
    class_id: int
    teacher_id: Optional[int]
    total_marks: int
    passing_marks: int
    credit_hours: int
    description: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Student Schemas ──────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    roll_number: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    class_id: int
    admission_date: Optional[date] = None


class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    parent_name: Optional[str] = None
    parent_phone: Optional[str] = None
    class_id: Optional[int] = None
    is_active: Optional[bool] = None


class StudentOut(BaseModel):
    id: int
    roll_number: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    parent_name: Optional[str]
    parent_phone: Optional[str]
    class_id: int
    admission_date: Optional[date]
    is_active: bool

    class Config:
        from_attributes = True


# ─── Teacher Schemas ──────────────────────────────────────────────────────────

class TeacherCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=6)
    employee_id: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    joining_date: Optional[date] = None
    base_salary: float = 0.0


class TeacherUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    base_salary: Optional[float] = None
    is_active: Optional[bool] = None


class TeacherOut(BaseModel):
    id: int
    employee_id: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date]
    gender: Optional[str]
    phone: Optional[str]
    qualification: Optional[str]
    specialization: Optional[str]
    joining_date: Optional[date]
    base_salary: float
    is_active: bool

    class Config:
        from_attributes = True


# ─── Result Schemas ───────────────────────────────────────────────────────────

class ResultCreate(BaseModel):
    student_id: int
    subject_id: int
    exam_type: str = Field(..., example="midterm")
    marks_obtained: float
    total_marks: float
    grade: Optional[GradeEnum] = None
    remarks: Optional[str] = None
    exam_date: Optional[date] = None


class ResultUpdate(BaseModel):
    marks_obtained: Optional[float] = None
    grade: Optional[GradeEnum] = None
    remarks: Optional[str] = None


class ResultOut(BaseModel):
    id: int
    student_id: int
    subject_id: int
    exam_type: str
    marks_obtained: float
    total_marks: float
    percentage: Optional[float] = None
    grade: Optional[GradeEnum]
    remarks: Optional[str]
    exam_date: Optional[date]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True

    @validator("percentage", always=True, pre=False)
    def compute_percentage(cls, v, values):
        mo = values.get("marks_obtained")
        tm = values.get("total_marks")
        if mo is not None and tm and tm > 0:
            return round((mo / tm) * 100, 2)
        return v


# ─── Report Card Schema ───────────────────────────────────────────────────────

class ReportCard(BaseModel):
    student: StudentOut
    results: List[ResultOut]
    total_marks_obtained: float
    total_marks: float
    overall_percentage: float
    overall_grade: str


# ─── Attendance Schemas ───────────────────────────────────────────────────────

class AttendanceCreate(BaseModel):
    student_id: int
    subject_id: int
    date: date
    status: AttendanceStatus = AttendanceStatus.present
    remarks: Optional[str] = None


class AttendanceBulkCreate(BaseModel):
    subject_id: int
    date: date
    records: List[dict]   # [{"student_id": 1, "status": "present"}, ...]


class AttendanceUpdate(BaseModel):
    status: Optional[AttendanceStatus] = None
    remarks: Optional[str] = None


class AttendanceOut(BaseModel):
    id: int
    student_id: int
    subject_id: int
    date: date
    status: AttendanceStatus
    remarks: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class AttendanceSummary(BaseModel):
    student_id: int
    subject_id: int
    total_classes: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_percentage: float


# ─── Fee Schemas ──────────────────────────────────────────────────────────────

class FeeCreate(BaseModel):
    student_id: int
    fee_type: str = Field(..., example="tuition")
    amount: float
    due_date: date
    month: Optional[str] = Field(None, example="January 2025")
    remarks: Optional[str] = None


class FeeUpdate(BaseModel):
    paid_date: Optional[date] = None
    paid_amount: Optional[float] = None
    status: Optional[FeeStatus] = None
    remarks: Optional[str] = None


class FeeOut(BaseModel):
    id: int
    student_id: int
    fee_type: str
    amount: float
    due_date: date
    paid_date: Optional[date]
    paid_amount: float
    status: FeeStatus
    month: Optional[str]
    remarks: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ─── Assignment Schemas ───────────────────────────────────────────────────────

class AssignmentCreate(BaseModel):
    subject_id: int
    title: str
    description: Optional[str] = None
    total_marks: float = 10.0
    due_date: datetime


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    total_marks: Optional[float] = None
    due_date: Optional[datetime] = None


class AssignmentOut(BaseModel):
    id: int
    subject_id: int
    title: str
    description: Optional[str]
    total_marks: float
    due_date: datetime
    created_by: int
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    assignment_id: int
    submission_text: Optional[str] = None
    file_url: Optional[str] = None


class SubmissionGrade(BaseModel):
    marks_obtained: float
    feedback: Optional[str] = None
    status: AssignmentStatus = AssignmentStatus.graded


class SubmissionOut(BaseModel):
    id: int
    assignment_id: int
    student_id: int
    submission_text: Optional[str]
    file_url: Optional[str]
    submitted_at: Optional[datetime]
    marks_obtained: Optional[float]
    status: AssignmentStatus
    feedback: Optional[str]

    class Config:
        from_attributes = True


# ─── Salary Schemas ───────────────────────────────────────────────────────────

class SalaryCreate(BaseModel):
    teacher_id: int
    month: str = Field(..., example="January 2025")
    base_salary: float
    allowances: float = 0.0
    deductions: float = 0.0
    remarks: Optional[str] = None


class SalaryUpdate(BaseModel):
    allowances: Optional[float] = None
    deductions: Optional[float] = None
    paid_date: Optional[date] = None
    status: Optional[SalaryStatus] = None
    remarks: Optional[str] = None


class SalaryOut(BaseModel):
    id: int
    teacher_id: int
    month: str
    base_salary: float
    allowances: float
    deductions: float
    net_salary: float
    paid_date: Optional[date]
    status: SalaryStatus
    remarks: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
