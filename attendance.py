from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from database.db import get_db
from models.models import Attendance, Student, Subject, Teacher, User, RoleEnum, AttendanceStatus
from schemas.schemas import (
    AttendanceCreate, AttendanceBulkCreate,
    AttendanceUpdate, AttendanceOut, AttendanceSummary
)
from utils.auth import require_admin_or_teacher, get_current_user

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/", response_model=AttendanceOut, status_code=201,
             summary="Mark attendance for one student")
def mark_attendance(
    data: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher)
):
    if not db.query(Student).filter(Student.id == data.student_id).first():
        raise HTTPException(status_code=404, detail="Student not found")
    if not db.query(Subject).filter(Subject.id == data.subject_id).first():
        raise HTTPException(status_code=404, detail="Subject not found")

    existing = db.query(Attendance).filter(
        Attendance.student_id == data.student_id,
        Attendance.subject_id == data.subject_id,
        Attendance.date == data.date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Attendance already marked for this date")

    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    att = Attendance(
        student_id=data.student_id,
        subject_id=data.subject_id,
        date=data.date,
        status=data.status,
        remarks=data.remarks,
        marked_by=teacher.id if teacher else None,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


@router.post("/bulk", summary="Mark attendance for a whole class at once")
def mark_bulk_attendance(
    data: AttendanceBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher)
):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    created, skipped = 0, 0
    for record in data.records:
        student_id = record.get("student_id")
        status_str = record.get("status", "present")
        try:
            status = AttendanceStatus(status_str)
        except ValueError:
            status = AttendanceStatus.present

        existing = db.query(Attendance).filter(
            Attendance.student_id == student_id,
            Attendance.subject_id == data.subject_id,
            Attendance.date == data.date
        ).first()
        if existing:
            skipped += 1
            continue

        att = Attendance(
            student_id=student_id,
            subject_id=data.subject_id,
            date=data.date,
            status=status,
            marked_by=teacher.id if teacher else None,
        )
        db.add(att)
        created += 1

    db.commit()
    return {"message": f"Marked {created} records, skipped {skipped} duplicates"}


@router.get("/", response_model=List[AttendanceOut], summary="Get attendance records")
def list_attendance(
    student_id: Optional[int] = Query(None),
    subject_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    status: Optional[AttendanceStatus] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Attendance)

    if current_user.role == RoleEnum.student:
        own = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not own:
            return []
        q = q.filter(Attendance.student_id == own.id)
    elif student_id:
        q = q.filter(Attendance.student_id == student_id)

    if subject_id:
        q = q.filter(Attendance.subject_id == subject_id)
    if date_from:
        q = q.filter(Attendance.date >= date_from)
    if date_to:
        q = q.filter(Attendance.date <= date_to)
    if status:
        q = q.filter(Attendance.status == status)

    return q.offset(skip).limit(limit).all()


@router.get("/summary/{student_id}/{subject_id}", response_model=AttendanceSummary,
            summary="Get attendance summary / percentage for a student in a subject")
def attendance_summary(
    student_id: int,
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Students can only view their own
    if current_user.role == RoleEnum.student:
        own = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not own or own.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")

    records = db.query(Attendance).filter(
        Attendance.student_id == student_id,
        Attendance.subject_id == subject_id
    ).all()

    total = len(records)
    present = sum(1 for r in records if r.status == AttendanceStatus.present)
    absent = sum(1 for r in records if r.status == AttendanceStatus.absent)
    late = sum(1 for r in records if r.status == AttendanceStatus.late)
    excused = sum(1 for r in records if r.status == AttendanceStatus.excused)
    pct = round((present / total) * 100, 2) if total > 0 else 0.0

    return AttendanceSummary(
        student_id=student_id,
        subject_id=subject_id,
        total_classes=total,
        present=present,
        absent=absent,
        late=late,
        excused=excused,
        attendance_percentage=pct
    )


@router.put("/{attendance_id}", response_model=AttendanceOut, summary="Update attendance record")
def update_attendance(attendance_id: int, data: AttendanceUpdate, db: Session = Depends(get_db),
                      _: User = Depends(require_admin_or_teacher)):
    att = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Record not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(att, field, value)
    db.commit()
    db.refresh(att)
    return att


@router.delete("/{attendance_id}", summary="Delete attendance record (Admin only)")
def delete_attendance(attendance_id: int, db: Session = Depends(get_db),
                      _: User = Depends(require_admin_or_teacher)):
    att = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not att:
        raise HTTPException(status_code=404, detail="Record not found")
    db.delete(att)
    db.commit()
    return {"message": "Record deleted"}
