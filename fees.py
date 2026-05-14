from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database.db import get_db
from models.models import Fee, Student, User, RoleEnum, FeeStatus
from schemas.schemas import FeeCreate, FeeUpdate, FeeOut
from utils.auth import require_admin, get_current_user

router = APIRouter(prefix="/fees", tags=["Fee Management"])


@router.post("/", response_model=FeeOut, status_code=201, summary="Create a fee entry")
def create_fee(data: FeeCreate, db: Session = Depends(get_db),
               _: User = Depends(require_admin)):
    if not db.query(Student).filter(Student.id == data.student_id).first():
        raise HTTPException(status_code=404, detail="Student not found")
    fee = Fee(**data.model_dump())
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return fee


@router.get("/", response_model=List[FeeOut], summary="List fee records")
def list_fees(
    student_id: Optional[int] = Query(None),
    status: Optional[FeeStatus] = Query(None),
    fee_type: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    q = db.query(Fee)

    if current_user.role == RoleEnum.student:
        own = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not own:
            return []
        q = q.filter(Fee.student_id == own.id)
    elif student_id:
        q = q.filter(Fee.student_id == student_id)

    if status:
        q = q.filter(Fee.status == status)
    if fee_type:
        q = q.filter(Fee.fee_type == fee_type)

    return q.offset(skip).limit(limit).all()


@router.get("/summary/{student_id}", summary="Fee summary for a student")
def fee_summary(student_id: int, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    if current_user.role == RoleEnum.student:
        own = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not own or own.id != student_id:
            raise HTTPException(status_code=403, detail="Access denied")

    fees = db.query(Fee).filter(Fee.student_id == student_id).all()
    total = sum(f.amount for f in fees)
    paid = sum(f.paid_amount for f in fees)
    pending = sum(f.amount for f in fees if f.status == FeeStatus.pending)
    overdue = sum(f.amount for f in fees if f.status == FeeStatus.overdue)

    return {
        "student_id": student_id,
        "total_fees": total,
        "total_paid": paid,
        "pending_amount": pending,
        "overdue_amount": overdue,
        "balance": total - paid
    }


@router.get("/{fee_id}", response_model=FeeOut, summary="Get fee by ID")
def get_fee(fee_id: int, db: Session = Depends(get_db),
            current_user: User = Depends(get_current_user)):
    fee = db.query(Fee).filter(Fee.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")
    if current_user.role == RoleEnum.student:
        own = db.query(Student).filter(Student.user_id == current_user.id).first()
        if not own or fee.student_id != own.id:
            raise HTTPException(status_code=403, detail="Access denied")
    return fee


@router.put("/{fee_id}", response_model=FeeOut, summary="Update fee / record payment")
def update_fee(fee_id: int, data: FeeUpdate, db: Session = Depends(get_db),
               _: User = Depends(require_admin)):
    fee = db.query(Fee).filter(Fee.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(fee, field, value)
    # Auto-update status
    if fee.paid_amount >= fee.amount:
        fee.status = FeeStatus.paid
    elif fee.paid_amount > 0:
        fee.status = FeeStatus.pending
    db.commit()
    db.refresh(fee)
    return fee


@router.delete("/{fee_id}", summary="Delete a fee record (Admin only)")
def delete_fee(fee_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    fee = db.query(Fee).filter(Fee.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee record not found")
    db.delete(fee)
    db.commit()
    return {"message": "Fee record deleted"}
