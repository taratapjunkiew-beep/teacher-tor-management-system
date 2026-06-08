import csv, io, json, shutil
from pathlib import Path
from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from .config import APP_NAME, SECRET_KEY, CURRICULUM_DIR
from .database import Base, engine, get_db, SessionLocal
from .models import Course, CurriculumFile, User
from .auth import authenticate, get_current_user, login_user, logout_user, hash_password
from .seed import seed_all
from .services.docx_generator import build_teaching_plan
from .services.pdf_importer import parse_courses_from_pdf

app = FastAPI(title=APP_NAME)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

def loads_filter(value):
    try:
        return json.loads(value or "[]")
    except Exception:
        return []
templates.env.filters["loads"] = loads_filter

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_all(db)
    finally:
        db.close()

def require_user(request: Request, db: Session) -> User:
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user

def require_admin(request: Request, db: Session) -> User:
    user = require_user(request, db)
    if user.role != "admin":
        raise HTTPException(status_code=403)
    return user

@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    return RedirectResponse("/dashboard" if get_current_user(request, db) else "/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return RedirectResponse("/dashboard", status_code=303)
    return templates.TemplateResponse("login.html", {"request":request, "app_name":APP_NAME, "error":""})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request":request, "app_name":APP_NAME, "error":"ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"}, status_code=401)
    login_user(request, user)
    return RedirectResponse("/dashboard", status_code=303)

@app.get("/logout")
def logout(request: Request):
    logout_user(request)
    return RedirectResponse("/login", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    return templates.TemplateResponse("dashboard.html", {
        "request":request, "app_name":APP_NAME, "user":user,
        "course_count": db.query(Course).count(),
        "verified_count": db.query(Course).filter(Course.is_verified == True).count(),
        "files_count": db.query(CurriculumFile).count(),
    })

@app.get("/create", response_class=HTMLResponse)
def create_page(request: Request, db: Session = Depends(get_db)):
    user = require_user(request, db)
    return templates.TemplateResponse("create.html", {"request":request, "app_name":APP_NAME, "user":user, "course":None, "error":""})

@app.post("/find-course", response_class=HTMLResponse)
def find_course(request: Request, course_code: str = Form(...), course_name: str = Form(""), db: Session = Depends(get_db)):
    user = require_user(request, db)
    code = course_code.strip()
    name = course_name.strip()
    course = db.query(Course).filter(Course.code == code, Course.is_active == True).first()
    if not course:
        error = f"ไม่พบรหัสวิชา {code} ในฐานข้อมูลหลักสูตรสำนักมาตรฯ ที่นำเข้าไว้ กรุณาให้แอดมินเพิ่มรายวิชานี้ก่อน ระบบจะไม่แต่งข้อมูลหลักสูตรเอง"
        return templates.TemplateResponse("create.html", {"request":request, "app_name":APP_NAME, "user":user, "course":None, "error":error, "input_code":code, "input_name":name})
    if name and name != course.name:
        # แสดงชื่อจากฐานข้อมูลเป็นหลัก
        pass
    return templates.TemplateResponse("create.html", {"request":request, "app_name":APP_NAME, "user":user, "course":course, "error":"", "input_code":code, "input_name":name})

@app.post("/generate")
def generate_plan(
    request: Request,
    course_code: str = Form(...),
    teacher_name: str = Form(...),
    position: str = Form("ครูพิเศษสอน"),
    college: str = Form("วิทยาลัยการอาชีพบ้านผือ"),
    db: Session = Depends(get_db)
):
    user = require_user(request, db)
    course = db.query(Course).filter(Course.code == course_code, Course.is_active == True).first()
    if not course:
        raise HTTPException(status_code=404, detail="ไม่พบรหัสวิชาในฐานข้อมูลหลักสูตร")
    path = build_teaching_plan(course, {"teacher_name":teacher_name, "position":position, "college":college})
    return FileResponse(path, filename=path.name, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

@app.get("/admin/courses", response_class=HTMLResponse)
def admin_courses(request: Request, db: Session = Depends(get_db)):
    user = require_admin(request, db)
    courses = db.query(Course).order_by(Course.code).all()
    return templates.TemplateResponse("admin_courses.html", {"request":request, "app_name":APP_NAME, "user":user, "courses":courses})

@app.get("/admin/courses/new", response_class=HTMLResponse)
def new_course(request: Request, db: Session = Depends(get_db)):
    user = require_admin(request, db)
    return templates.TemplateResponse("course_form.html", {"request":request, "app_name":APP_NAME, "user":user, "course":None})

@app.get("/admin/courses/{course_id}/edit", response_class=HTMLResponse)
def edit_course(course_id: int, request: Request, db: Session = Depends(get_db)):
    user = require_admin(request, db)
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course: raise HTTPException(status_code=404)
    return templates.TemplateResponse("course_form.html", {"request":request, "app_name":APP_NAME, "user":user, "course":course})

@app.post("/admin/courses/save")
def save_course(
    request: Request, course_id: int = Form(0), code: str = Form(...), name: str = Form(...),
    level: str = Form("ปวช."), curriculum: str = Form("หลักสูตรประกาศนียบัตรวิชาชีพ พุทธศักราช 2567"),
    program_type: str = Form(""), occupational_group: str = Form(""), major: str = Form(""),
    theory_hours: int = Form(1), practice_hours: int = Form(3), credits: int = Form(2),
    standard_ref: str = Form(""), learning_outcome: str = Form(""), objectives: str = Form(""),
    competencies: str = Form(""), description: str = Form(""), occupational_standard: str = Form(""),
    assessment: str = Form(""), source_note: str = Form(""), is_verified: str = Form("off"), is_active: str = Form("on"),
    db: Session = Depends(get_db)
):
    user = require_admin(request, db)
    course = db.query(Course).filter(Course.id == course_id).first() if course_id else Course()
    if not course_id: db.add(course)

    def lines_to_json(text):
        return json.dumps([x.strip() for x in text.splitlines() if x.strip()], ensure_ascii=False)
    course.code=code.strip(); course.name=name.strip(); course.level=level; course.curriculum=curriculum
    course.program_type=program_type; course.occupational_group=occupational_group; course.major=major
    course.theory_hours=theory_hours; course.practice_hours=practice_hours; course.credits=credits
    course.standard_ref=standard_ref; course.learning_outcome=learning_outcome
    course.objectives=lines_to_json(objectives); course.competencies=lines_to_json(competencies)
    course.description=description; course.occupational_standard=occupational_standard
    course.assessment=assessment; course.source_note=source_note
    course.is_verified=(is_verified=="on"); course.is_active=(is_active=="on")
    db.commit()
    return RedirectResponse("/admin/courses", status_code=303)

@app.get("/admin/import", response_class=HTMLResponse)
def import_page(request: Request, db: Session = Depends(get_db)):
    user = require_admin(request, db)
    return templates.TemplateResponse("admin_import.html", {"request":request, "app_name":APP_NAME, "user":user, "message":""})

@app.post("/admin/import/csv", response_class=HTMLResponse)
async def import_csv(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = require_admin(request, db)
    content = (await file.read()).decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(content))
    count = 0
    for row in reader:
        code = (row.get("code") or "").strip()
        if not code: continue
        course = db.query(Course).filter(Course.code == code).first()
        if not course:
            course = Course(code=code)
            db.add(course)
        course.name = row.get("name","").strip()
        course.level = row.get("level","ปวช.")
        course.curriculum = row.get("curriculum","หลักสูตรประกาศนียบัตรวิชาชีพ พุทธศักราช 2567")
        course.program_type = row.get("program_type","")
        course.occupational_group = row.get("occupational_group","")
        course.major = row.get("major","")
        course.theory_hours = int(row.get("theory_hours") or 1)
        course.practice_hours = int(row.get("practice_hours") or 3)
        course.credits = int(row.get("credits") or 2)
        course.standard_ref = row.get("standard_ref","")
        course.learning_outcome = row.get("learning_outcome","")
        course.objectives = json.dumps([x.strip() for x in row.get("objectives","").split("|") if x.strip()], ensure_ascii=False)
        course.competencies = json.dumps([x.strip() for x in row.get("competencies","").split("|") if x.strip()], ensure_ascii=False)
        course.description = row.get("description","")
        course.occupational_standard = row.get("occupational_standard","")
        course.assessment = row.get("assessment","")
        course.source_note = row.get("source_note","CSV import")
        course.is_verified = True
        course.is_active = True
        count += 1
    db.commit()
    return templates.TemplateResponse("admin_import.html", {"request":request, "app_name":APP_NAME, "user":user, "message":f"นำเข้าสำเร็จ {count} รายวิชา"})


@app.get("/admin/pdf-import", response_class=HTMLResponse)
def pdf_import_page(request: Request, db: Session = Depends(get_db)):
    user = require_admin(request, db)
    return templates.TemplateResponse("admin_pdf_import.html", {"request":request, "app_name":APP_NAME, "user":user, "message":"", "courses":[]})

@app.post("/admin/pdf-import/upload", response_class=HTMLResponse)
async def pdf_import_upload(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = require_admin(request, db)
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="รองรับเฉพาะไฟล์ PDF")
    safe_name = file.filename.replace("/", "_").replace("\\", "_")
    dest = CURRICULUM_DIR / safe_name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    record = CurriculumFile(filename=file.filename, saved_path=str(dest), uploaded_by_id=user.id)
    db.add(record)

    result = parse_courses_from_pdf(dest)
    imported = 0
    updated = 0
    for row in result["courses"]:
        course = db.query(Course).filter(Course.code == row["code"]).first()
        is_new = course is None
        if is_new:
            course = Course(code=row["code"])
            db.add(course)
        course.name = row["name"]
        course.level = row["level"]
        course.curriculum = row["curriculum"]
        course.program_type = row["program_type"]
        course.occupational_group = row["occupational_group"]
        course.major = row["major"]
        course.theory_hours = row["theory_hours"]
        course.practice_hours = row["practice_hours"]
        course.credits = row["credits"]
        course.standard_ref = row["standard_ref"]
        course.learning_outcome = row["learning_outcome"]
        course.objectives = json.dumps(row["objectives"], ensure_ascii=False)
        course.competencies = json.dumps(row["competencies"], ensure_ascii=False)
        course.description = row["description"]
        course.occupational_standard = row["occupational_standard"]
        course.assessment = row["assessment"]
        course.source_note = row["source_note"]
        course.units = json.dumps(row["units"], ensure_ascii=False)
        course.is_verified = row["is_verified"]
        course.is_active = True
        if is_new:
            imported += 1
        else:
            updated += 1

    db.commit()
    msg = f"นำเข้าอัตโนมัติสำเร็จ: เพิ่มใหม่ {imported} วิชา, อัปเดต {updated} วิชา จากไฟล์ {file.filename}"
    return templates.TemplateResponse("admin_pdf_import.html", {"request":request, "app_name":APP_NAME, "user":user, "message":msg, "courses":result["courses"][:80]})


@app.get("/admin/users", response_class=HTMLResponse)
def users(request: Request, db: Session = Depends(get_db)):
    user = require_admin(request, db)
    users = db.query(User).order_by(User.username).all()
    return templates.TemplateResponse("admin_users.html", {"request":request, "app_name":APP_NAME, "user":user, "users":users})

@app.post("/admin/users/create")
def create_user(request: Request, username: str = Form(...), full_name: str = Form(""), password: str = Form(...), role: str = Form("teacher"), db: Session = Depends(get_db)):
    admin = require_admin(request, db)
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="มีผู้ใช้นี้แล้ว")
    db.add(User(username=username, full_name=full_name, password_hash=hash_password(password), role=role, is_active=True))
    db.commit()
    return RedirectResponse("/admin/users", status_code=303)
