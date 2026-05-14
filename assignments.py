from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database.db import get_db
from models.models import (
    Assignment, AssignmentSubmission, Student,
    Teacher, Subject, User, RoleEnum, AssignmentStatus
)
from schemas.schemas import (
    AssignmentCreate, AssignmentUpdate, AssignmentOut,
    SubmissionCreate, SubmissionGrade, SubmissionOut
)
from utils.auth import require_admin, require_admin_or_teacher, get_current_user

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post("/", response_model=AssignmentOut, status_code=201,
             summary="Create an assignment (Teacher / Admin)")
def create_assignment(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_teacher)
):
    if not db.query(Subject).filter(Subject.id == data.subject_id).first():
        raise HTTPException(status_code=404, detail="Subject not found")

    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    teacher_id = teacher.id if teacher else 1  # fallback for admin

    assignment = Assignment(
        subject_id=data.subject_id,
        title=data.title,
        description=data.description,
        total_marks=data.total_marks,
        due_date=data.due_date,
        created_by=teacher_id,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/", response_model=List[AssignmentOut], summary="List assignments")
def list_assignments(
    subject_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user)
):
    q = db.query(Assignment)
    if subject_id:
        q = q.filter(Assignment.subject_id == subject_id)
    return q.offset(skip).limit(limit).all()


@router.get("/{assignment_id}", response_model=AssignmentOut, summary="Get assignment by ID")
def get_assignment(assignment_id: int, db: Session = Depends(get_db),
                   _: User = Depends(get_current_user)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.put("/{assignment_id}", response_model=AssignmentOut, summary="Update an assignment")
def update_assignment(assignment_id: int, data: AssignmentUpdate, db: Session = Depends(get_db),
                      _: User = Depends(require_admin_or_teacher)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(assignment, field, value)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", summary="Delete an assignment")
def delete_assignment(assignment_id: int, db: Session = Depends(get_db),
                      _: User = Depends(require_admin_or_teacher)):
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    db.delete(assignment)
    db.commit()
    return {"message": "Assignment deleted"}


# ─── Submissions ──────────────────────────────────────────────────────────────

@router.post("/submit", response_model=SubmissionOut, status_code=201,
             summary="Submit an assignment (Student)")
def submit_assignment(
    data: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [RoleEnum.student, RoleEnum.admin]:
        raise HTTPException(status_code=403, detail="Only students can submit assignments")

    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=404, detail="Student profile not found")

    assignment = db.query(Assignment).filter(Assignment.id == data.assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    existing = db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == data.assignment_id,
        AssignmentSubmission.student_id == student.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already submitted")

    from datetime import datetime
    status = AssignmentStatus.late if datetime.utcnow() > assignment.due_date else AssignmentStatus.submitted

    submission = AssignmentSubmission(
        assignment_id=data.assignment_id,
        student_id=student.id,
        submission_text=data.submission_text,
        file_url=data.file_url,
        status=status,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


@router.get("/{assignment_id}/submissions", response_model=List[SubmissionOut],
            summary="Get all submissions for an assignment (Teacher / Admin)")
def get_submissions(assignment_id: int, db: Session = Depends(get_db),
                    _: User = Depends(require_admin_or_teacher)):
    return db.query(AssignmentSubmission).filter(
        AssignmentSubmission.assignment_id == assignment_id
    ).all()


@router.put("/submissions/{submission_id}/grade", response_model=SubmissionOut,
            summary="Grade a submission (Teacher / Admin)")
def grade_submission(
    submission_id: int,
    data: SubmissionGrade,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_or_teacher)
):
    sub = db.query(AssignmentSubmission).filter(AssignmentSubmission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    sub.marks_obtained = data.marks_obtained
    sub.feedback = data.feedback
    sub.status = data.status
    db.commit()
    db.refresh(sub)
    return sub


@router.get("/my/submissions", response_model=List[SubmissionOut],
            summary="Student: get all my submissions")
def my_submissions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    student = db.query(Student).filter(Student.user_id == current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return db.query(AssignmentSubmission).filter(
        AssignmentSubmission.student_id == student.id
    ).all()
