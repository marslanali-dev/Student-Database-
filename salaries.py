from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database.db import get_db
from models.models import Salary, Teacher, User, RoleEnum, SalaryStatus
from schemas.schemas import SalaryCreate, SalaryUpdate, SalaryOut
from utils.auth import require_admin, get_current_user

router = APIRouter(prefix="/salaries", tags=["Teacher Salary"])


@router.post("/", response_model=SalaryOut, status_code=201,
             summary="Generate salary for a teacher (Admin only)")
def create_salary(data: SalaryCreate, db: Session = Depends(get_db),
                  _: User = Depends(require_admin)):
    teacher = db.query(Teacher).filter(Teacher.id == data.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")

    existing = db.query(Salary).filter(
        Salary.teacher_id == data.teacher_id,
        Salary.month == data.month
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Salary for this month already generated")

    net = data.base_salary + data.allowances - data.deductions
    salary = Salary(
        teacher_id=data.teacher_id,
        month=data.month,
        base_salary=data.base_salary,
        allowances=data.allowances,
        deductions=data.deductions,
        net_salary=net,
        remarks=data.remarks,
    )
    db.add(salary)
    db.commit()
    db.refresh(salary)
    return salary


@router.post("/bulk", summary="Generate salaries for all active teachers for a month")
def bulk_generate_salaries(
    month: str = Query(..., example="January 2025"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin)
):
    teachers = db.query(Teacher).filter(Teacher.is_active == True).all()
    created, skipped = 0, 0
    for teacher in teachers:
        existing = db.query(Salary).filter(
            Salary.teacher_id == teacher.id,
            Salary.month == month
        ).first()
        if existing:
            skipped += 1
            continue
        net = teacher.base_salary
        salary = Salary(
            teacher_id=teacher.id,
            month=month,
            base_salary=teacher.base_salary,
            allowances=0.0,
            deductions=0.0,
            net_salary=net,
        )
        db.add(salary)
        created += 1
    db.commit()
    return {"message": f"Generated {created} salaries, skipped {skipped} (already exist)"}


@router.get("/", response_model=List[SalaryOut], summary="List salary records")
def list_salaries(
    teacher_id: Optional[int] = Query(None),
    month: Optional[str] = Query(None),
    status: Optional[SalaryStatus] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Salary)

    # Teachers can only view their own salary
    if current_user.role == RoleEnum.teacher:
        teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
        if not teacher:
            return []
        q = q.filter(Salary.teacher_id == teacher.id)
    elif teacher_id:
        q = q.filter(Salary.teacher_id == teacher_id)

    if month:
        q = q.filter(Salary.month == month)
    if status:
        q = q.filter(Salary.status == status)

    return q.offset(skip).limit(limit).all()


@router.get("/my", response_model=List[SalaryOut], summary="Teacher: view own salary history")
def my_salaries(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher profile not found")
    return db.query(Salary).filter(Salary.teacher_id == teacher.id).all()


@router.get("/summary/{teacher_id}", summary="Annual salary summary for a teacher")
def salary_summary(teacher_id: int, year: str = Query(..., example="2025"),
                   db: Session = Depends(get_db), _: User = Depends(require_admin)):
    salaries = db.query(Salary).filter(
        Salary.teacher_id == teacher_id,
        Salary.month.contains(year)
    ).all()
    total_net = sum(s.net_salary for s in salaries)
    total_paid = sum(s.net_salary for s in salaries if s.status == SalaryStatus.paid)
    total_pending = sum(s.net_salary for s in salaries if s.status == SalaryStatus.pending)

    return {
        "teacher_id": teacher_id,
        "year": year,
        "months_generated": len(salaries),
        "total_net_salary": total_net,
        "total_paid": total_paid,
        "total_pending": total_pending,
    }


@router.get("/{salary_id}", response_model=SalaryOut, summary="Get salary record by ID")
def get_salary(salary_id: int, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    salary = db.query(Salary).filter(Salary.id == salary_id).first()
    if not salary:
        raise HTTPException(status_code=404, detail="Salary record not found")
    if current_user.role == RoleEnum.teacher:
        teacher = db.query(Teacher).filter(Teacher.user_id == current_user.id).first()
        if not teacher or salary.teacher_id != teacher.id:
            raise HTTPException(status_code=403, detail="Access denied")
    return salary


@router.put("/{salary_id}", response_model=SalaryOut, summary="Update salary / mark as paid")
def update_salary(salary_id: int, data: SalaryUpdate, db: Session = Depends(get_db),
                  _: User = Depends(require_admin)):
    salary = db.query(Salary).filter(Salary.id == salary_id).first()
    if not salary:
        raise HTTPException(status_code=404, detail="Salary record not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(salary, field, value)
    # Recalculate net salary if allowances or deductions changed
    salary.net_salary = salary.base_salary + salary.allowances - salary.deductions
    db.commit()
    db.refresh(salary)
    return salary


@router.delete("/{salary_id}", summary="Delete a salary record (Admin only)")
def delete_salary(salary_id: int, db: Session = Depends(get_db),
                  _: User = Depends(require_admin)):
    salary = db.query(Salary).filter(Salary.id == salary_id).first()
    if not salary:
        raise HTTPException(status_code=404, detail="Salary record not found")
    db.delete(salary)
    db.commit()
    return {"message": "Salary record deleted"}
