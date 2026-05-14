from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database.db import get_db
from models.models import Class, Subject, User
from schemas.schemas import ClassCreate, ClassOut, SubjectCreate, SubjectUpdate, SubjectOut
from utils.auth import require_admin, require_admin_or_teacher

router = APIRouter(tags=["Classes & Subjects"])


# ─── Classes ──────────────────────────────────────────────────────────────────

@router.post("/classes", response_model=ClassOut, status_code=201, summary="Create a class")
def create_class(data: ClassCreate, db: Session = Depends(get_db),
                 _: User = Depends(require_admin)):
    existing = db.query(Class).filter(
        Class.name == data.name,
        Class.section == data.section,
        Class.academic_year == data.academic_year
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Class already exists")
    cls = Class(**data.model_dump())
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


@router.get("/classes", response_model=List[ClassOut], summary="List all classes")
def list_classes(db: Session = Depends(get_db), _: User = Depends(require_admin_or_teacher)):
    return db.query(Class).all()


@router.get("/classes/{class_id}", response_model=ClassOut, summary="Get class by ID")
def get_class(class_id: int, db: Session = Depends(get_db),
              _: User = Depends(require_admin_or_teacher)):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    return cls


@router.delete("/classes/{class_id}", summary="Delete a class (Admin only)")
def delete_class(class_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    db.delete(cls)
    db.commit()
    return {"message": "Class deleted"}


# ─── Subjects ─────────────────────────────────────────────────────────────────

@router.post("/subjects", response_model=SubjectOut, status_code=201, summary="Create a subject")
def create_subject(data: SubjectCreate, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    if db.query(Subject).filter(Subject.code == data.code).first():
        raise HTTPException(status_code=400, detail="Subject code already exists")
    subject = Subject(**data.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.get("/subjects", response_model=List[SubjectOut], summary="List all subjects")
def list_subjects(db: Session = Depends(get_db), _: User = Depends(require_admin_or_teacher)):
    return db.query(Subject).all()


@router.get("/subjects/{subject_id}", response_model=SubjectOut, summary="Get subject by ID")
def get_subject(subject_id: int, db: Session = Depends(get_db),
                _: User = Depends(require_admin_or_teacher)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


@router.put("/subjects/{subject_id}", response_model=SubjectOut, summary="Update subject")
def update_subject(subject_id: int, data: SubjectUpdate, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/subjects/{subject_id}", summary="Delete a subject (Admin only)")
def delete_subject(subject_id: int, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(subject)
    db.commit()
    return {"message": "Subject deleted"}
