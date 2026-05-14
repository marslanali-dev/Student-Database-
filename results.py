from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database.db import get_db
from models.models import Result, Student, Subject, User, RoleEnum
from schemas.schemas import ResultCreate, ResultUpdate, ResultOut, ReportCard
from utils.auth import (
    require_admin, require_admin_or_teacher,
    get_current_user, calculate_grade
)

router = APIRouter(prefix="/results", tags=["Results & Report Cards"])


@router.post("/", response_model=ResultOut, status_code=201, summary="Add exam result")
def add_result(data: ResultCreate, db: Session = Depends(get_db),
               _: User = Depends(require_admin_or_teacher)):
    if not db.query(Student).filter(Student.id == data.student_id).first():
        raise HTTPException(status_code=404, detail="Student not found")
    if not db.query(Subject).filter(Subject.id == data.subject_id).first():
        raise HTTPException(status_code=404, detail="Subject not found")

    existing = db.query(Result).filter(
        Result.student_id == data.student_id,
        Result.subject_id == data.subject_id,
        Result.exam_type == data.exam_type
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Result already exists for this exam")

    # Auto-calculate grade if not provided
    grade = data.grade
    if not grade and data.total_marks > 0:
        pct = (data.marks_obtained / data.total_marks) * 100
        grade = calculate_grade(pct)

    result = Result(
        student_id=data.student_id,
        subject_id=data.subject_id,
        exam_type=data.exam_type,
        marks_obtained=data.marks_obtained,
        total_marks=data.total_marks,
        grade=grade,
        remarks=data.remarks,
        exam_date=data.exam_date,
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@router.get("/", response_model=List[ResultOut], summary="List results with filters")
def list_results(
    student_id: Optional[int] = Query(None),
    subject_id: Optional[int] = Query(None),
    exam_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Result)

    # Students can only see their own results
    if current_user.role == RoleEnum.student:
        own = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not own:
            return []
        q = q.filter(Result.student_id == own.id)
    elif student_id:
        q = q.filter(Result.student_id == student_id)

    if subject_id:
        q = q.filter(Result.subject_id == subject_id)
    if exam_type:
        q = q.filter(Result.exam_type == exam_type)

    results = q.all()
    # Attach percentage
    for r in results:
        if r.total_marks > 0:
            r.percentage = round((r.marks_obtained / r.total_marks) * 100, 2)
    return results


@router.get("/report-card/{student_id}", response_model=ReportCard,
            summary="Generate full report card for a student")
def get_report_card(
    student_id: int,
    exam_type: Optional[str] = Query(None, description="Filter by exam type e.g. 'final'"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Students can only get their own report card
    if current_user.role == RoleEnum.student:
        own = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not own or own.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")

    q = db.query(Result).filter(Result.student_id == student_id)
    if exam_type:
        q = q.filter(Result.exam_type == exam_type)
    results = q.all()

    total_obtained = sum(r.marks_obtained for r in results)
    total_marks = sum(r.total_marks for r in results)
    overall_pct = round((total_obtained / total_marks * 100), 2) if total_marks > 0 else 0.0
    overall_grade = calculate_grade(overall_pct)

    # Attach percentage to each result
    result_outs = []
    for r in results:
        ro = ResultOut.model_validate(r)
        ro.percentage = round((r.marks_obtained / r.total_marks) * 100, 2) if r.total_marks > 0 else 0
        result_outs.append(ro)

    from schemas.schemas import StudentOut
    return ReportCard(
        student=StudentOut.model_validate(student),
        results=result_outs,
        total_marks_obtained=total_obtained,
        total_marks=total_marks,
        overall_percentage=overall_pct,
        overall_grade=overall_grade,
    )


@router.put("/{result_id}", response_model=ResultOut, summary="Update a result")
def update_result(result_id: int, data: ResultUpdate, db: Session = Depends(get_db),
                  _: User = Depends(require_admin_or_teacher)):
    result = db.query(Result).filter(Result.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(result, field, value)
    if data.marks_obtained is not None:
        pct = (result.marks_obtained / result.total_marks) * 100
        result.grade = calculate_grade(pct)
    db.commit()
    db.refresh(result)
    return result


@router.delete("/{result_id}", summary="Delete a result (Admin only)")
def delete_result(result_id: int, db: Session = Depends(get_db),
                  _: User = Depends(require_admin)):
    result = db.query(Result).filter(Result.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    db.delete(result)
    db.commit()
    return {"message": "Result deleted"}
