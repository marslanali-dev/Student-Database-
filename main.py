from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database.db import engine, Base
from models import models  # ensures all models are registered
from routers import (
    auth_router, students_router, teachers_router,
    classes_router, results_router, attendance_router,
    fees_router, assignments_router, salaries_router
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables on startup
    Base.metadata.create_all(bind=engine)
    # Seed a default admin if none exists
    _seed_admin()
    yield


def _seed_admin():
    from database.db import SessionLocal
    from models.models import User, RoleEnum
    from utils.auth import hash_password
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.role == RoleEnum.admin).first():
            admin = User(
                username="admin",
                email="admin@school.com",
                hashed_password=hash_password("admin123"),
                role=RoleEnum.admin,
            )
            db.add(admin)
            db.commit()
            print("✅  Default admin created  →  username: admin  |  password: admin123")
    finally:
        db.close()


app = FastAPI(
    title="🏫 School Management System API",
    description="""
## School Management System — Full Backend

A production-ready REST API built with **FastAPI** covering every aspect of school operations.

### 🔐 Authentication & Authorization
- JWT Bearer token authentication
- Role-based access control (RBAC): **Admin**, **Teacher**, **Student**, **Parent**

### 📚 Modules
| Module | Description |
|---|---|
| **Auth** | Login, register, change password, user management |
| **Students** | Enroll, list, update, deactivate students |
| **Teachers** | Add, manage teacher profiles |
| **Classes & Subjects** | Create classes, assign subjects and teachers |
| **Results / Report Card** | Record exam marks, auto-grade, generate report cards |
| **Attendance** | Mark individual or bulk attendance, summaries & percentages |
| **Fees** | Create fees, record payments, fee summaries |
| **Assignments** | Create, submit, grade assignments |
| **Salaries** | Generate, update, bulk-process teacher salaries |

### 🚀 Quick Start
1. Login with **admin / admin123** to get a JWT token
2. Use the token in `Authorize` (top right) for all subsequent requests
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={"name": "School Admin", "email": "admin@school.com"},
    license_info={"name": "MIT"},
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(students_router)
app.include_router(teachers_router)
app.include_router(classes_router)
app.include_router(results_router)
app.include_router(attendance_router)
app.include_router(fees_router)
app.include_router(assignments_router)
app.include_router(salaries_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "🏫 School Management System API",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
