from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database.db import get_db
from models.models import Teacher, User, RoleEnum
from schemas.schemas import TeacherCreate, TeacherUpdate, TeacherOut
from utils.auth import hash_password, require_admin, require_admin_or_teacher, get_current_user

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post("/", response_model=TeacherOut, status_code=201, summary="Add a new teacher")
def create_teacher(data: TeacherCreate, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(Teacher).filter(Teacher.employee_id == data.employee_id).first():
        raise HTTPException(status_code=400, detail="Employee ID already exists")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=RoleEnum.teacher
    )
    db.add(user)
    db.flush()

    teacher = Teacher(
        user_id=user.id,
        employee_id=data.employee_id,
        first_name=data.first_name,
        last_name=data.last_name,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        address=data.address,
        phone=data.phone,
        qualification=data.qualification,
        specialization=data.specialization,
        joining_date=data.joining_date,
        base_salary=data.base_salary,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.get("/", response_model=List[TeacherOut], summary="List all teachers")
def list_teachers(
    is_active: Optional[bool] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teacher)
):
    q = db.query(Teacher)
    if is_active is not None:
        q = q.filter(Teacher.is_active == is_active)
    return q.offset(skip).limit(limit).all()


@router.get("/me", response_model=TeacherOut, summary="Get own teacher profile")
def my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")
    return teacher


@router.get("/{teacher_id}", response_model=TeacherOut, summary="Get teacher by ID")
def get_teacher(teacher_id: int, db: Session = Depends(get_db),
                _: User = Depends(require_admin_or_teacher)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return teacher


@router.put("/{teacher_id}", response_model=TeacherOut, summary="Update teacher info")
def update_teacher(teacher_id: int, data: TeacherUpdate, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(teacher, field, value)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}", summary="Remove a teacher (Admin only)")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    db.delete(teacher)
    db.commit()
    return {"message": "Teacher deleted"}
