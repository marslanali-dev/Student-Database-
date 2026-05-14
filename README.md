# 🏫 School Management System — FastAPI Backend

A full-featured, production-ready school management REST API built with **FastAPI**, **SQLAlchemy**, and **JWT authentication**.

---

## 🚀 Features

| Module | Endpoints | Roles |
|---|---|---|
| **Authentication** | Login, Register, Change Password | All |
| **Students** | CRUD + enrollment | Admin, Teacher (read), Student (self) |
| **Teachers** | CRUD + profile | Admin, Teacher (self) |
| **Classes & Subjects** | CRUD + assignment | Admin |
| **Results / Report Card** | Add marks, auto-grade, full report card | Admin, Teacher (write), Student (read) |
| **Attendance** | Individual + bulk mark, summaries | Admin, Teacher (write), Student (read) |
| **Fees** | Create, pay, summaries | Admin (write), Student (read own) |
| **Assignments** | Create, submit, grade | Teacher/Admin (create/grade), Student (submit) |
| **Salaries** | Generate, bulk process, pay | Admin (write), Teacher (read own) |

---

## 🔐 Roles & Access

| Role | Access |
|---|---|
| `admin` | Full access to everything |
| `teacher` | Read students, mark attendance, add results, create assignments, view own salary |
| `student` | View own profile, results, attendance, fees, submit assignments |
| `parent` | (Extensible — view student info) |

---

## 📦 Installation

```bash
# 1. Clone / unzip the project
cd school_management

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔑 Default Admin Credentials

On first run, the system automatically creates an admin account:

```
Username : admin
Password : admin123
```

> ⚠️ Change this immediately in production!

---

## 📖 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔄 Typical Workflow

```
1. POST /auth/login          → Get JWT token
2. POST /classes             → Create Grade 10-A
3. POST /subjects            → Add Math, Science subjects
4. POST /teachers            → Add teacher profiles
5. PUT  /subjects/{id}       → Assign teacher to subject
6. POST /students            → Enroll students
7. POST /attendance          → Mark daily attendance
8. POST /attendance/bulk     → Mark whole class at once
9. POST /results             → Enter exam marks
10. GET /results/report-card/{student_id} → Full report card
11. POST /fees               → Create monthly fee entries
12. PUT  /fees/{id}          → Record payment
13. POST /assignments        → Create homework
14. POST /assignments/submit → Student submits
15. PUT  /assignments/submissions/{id}/grade → Teacher grades
16. POST /salaries           → Generate monthly salary
17. POST /salaries/bulk      → Generate for all teachers at once
18. PUT  /salaries/{id}      → Mark as paid
```

---

## 📂 Project Structure

```
school_management/
├── main.py                  # App entry point, router registration
├── requirements.txt
├── .env                     # Environment variables
├── database/
│   └── db.py               # SQLAlchemy engine & session
├── models/
│   └── models.py           # All ORM models (11 tables)
├── schemas/
│   └── schemas.py          # Pydantic request/response schemas
├── routers/
│   ├── auth.py             # /auth/* endpoints
│   ├── students.py         # /students/* endpoints
│   ├── teachers.py         # /teachers/* endpoints
│   ├── classes.py          # /classes/* & /subjects/* endpoints
│   ├── results.py          # /results/* + report card
│   ├── attendance.py       # /attendance/* + bulk + summary
│   ├── fees.py             # /fees/* + fee summary
│   ├── assignments.py      # /assignments/* + submissions
│   └── salaries.py         # /salaries/* + bulk generate
└── utils/
    └── auth.py             # JWT, hashing, RBAC dependencies
```

---

## 🗄️ Database Models

```
users ──────────┬── students ──┬── results
                │              ├── attendances
                │              ├── fees
                │              └── assignment_submissions
                │
                └── teachers ──┬── subjects ──┬── results
                               │              ├── attendances
                               │              └── assignments ── assignment_submissions
                               └── salaries

classes ── students
        └── subjects
```

---

## ⚙️ Environment Variables (.env)

```env
SECRET_KEY=your-super-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./school.db
# For PostgreSQL: postgresql://user:password@localhost/school_db
```

---

## 🏭 Production Tips

1. **Replace SQLite** with PostgreSQL: set `DATABASE_URL` in `.env`
2. **Use Alembic** for database migrations
3. **Set a strong** `SECRET_KEY`
4. **Add rate limiting** with `slowapi`
5. **Run with Gunicorn**: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`
