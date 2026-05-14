from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database.db import get_db
from models.models import Student, User, RoleEnum
from schemas.schemas import StudentCreate, StudentUpdate, StudentOut
from utils.auth import hash_password, require_admin, require_admin_or_teacher, get_current_user

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/", response_model=StudentOut, status_code=201, summary="Enroll a new student")
def create_student(data: StudentCreate, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    # Create user account
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(Student).filter(Student.roll_number == data.roll_number).first():
        raise HTTPException(status_code=400, detail="Roll number already exists")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=RoleEnum.student
    )
    db.add(user)
    db.flush()

    student = Student(
        user_id=user.id,
        roll_number=data.roll_number,
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        address=data.address,
        phone=data.phone,
        parent_name=data.parent_name,
        parent_phone=data.parent_phone,
        class_id=data.class_id,
        admission_date=data.admission_date,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.get("/", response_model=List[StudentOut], summary="List all students")
def list_students(
    class_id: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teacher)
):
    q = db.query(Student)
    if class_id:
        q = q.filter(Student.class_id == class_id)
    if is_active is not None:
        q = q.filter(Student.is_active == is_active)
    return q.offset(skip).limit(limit).all()


@router.get("/me", response_model=StudentOut, summary="Get own student profile")
def my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return student


@router.get("/{student_id}", response_model=StudentOut, summary="Get student by ID")
def get_student(student_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    # Students can only view their own profile
    if current_user.role == RoleEnum.student:
        own = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not own or own.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
    return student


@router.put("/{student_id}", response_model=StudentOut, summary="Update student info")
def update_student(student_id: int, data: StudentUpdate, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/{student_id}", summary="Remove a student (Admin only)")
def delete_student(student_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"message": "Student deleted"}
