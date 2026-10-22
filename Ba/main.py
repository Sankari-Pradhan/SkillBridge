from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone, timedelta
from pypdf import PdfReader



import secrets
from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


from pydantic import BaseModel, EmailStr

from pwdlib import PasswordHash

from pathlib import Path

import os
import jwt

from sqlalchemy import text
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

import io
import re
import sys
import threading
import time
import webbrowser

from fastapi import Depends

#==========================================
# PostgreSQL Database Connection
#==========================================

DATABASE_URL = os.getenv("DATABASE_URL")

engine = None

if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://", "postgresql://", 1
    )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )


password_hash = PasswordHash.recommended()
bearer_scheme = HTTPBearer()

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(user_id: int, email: str) -> str:
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured")

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        secret_key,
        algorithm=JWT_ALGORITHM
    )


def verify_access_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise HTTPException(
            status_code=500,
            detail="JWT secret is not configured."
        )

    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload."
            )

        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token."
        )


#==========================================
# SKILLBRIDGE APPLICATION
#==========================================

app = FastAPI(
    title="SkillBridge",
    description="Your Personal Career and Learning Assistant",
    version="1.0.0"
)



def verify_admin_key(x_admin_key: str = Header(...)):
    expected_key = os.getenv("ADMIN_API_KEY")

    if not expected_key or not secrets.compare_digest(
        x_admin_key, expected_key
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid admin key"
        )

    return True



@app.get("/api/me")
def get_current_user(
    payload: dict = Depends(verify_access_token)
):
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload."
        )

    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    try:
        with engine.connect() as connection:
            user = connection.execute(
                text("""
                    SELECT id, name, email
                    FROM users
                    WHERE id = :user_id
                """),
                {"user_id": int(user_id)}
            ).mappings().first()

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="User not found."
            )

        return {
            "success": True,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
        }

    except HTTPException:
        raise
    except (SQLAlchemyError, ValueError):
        import logging
        logging.exception("Could not retrieve current user")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve user."
        )



@app.get("/api/admin/users")
def list_users(
    admin: bool = Depends(verify_admin_key)
):
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT id, name, email, created_at
                    FROM users
                    ORDER BY id DESC
                """)
            )

            users = [
                {
                    "id": row.id,
                    "name": row.name,
                    "email": row.email,
                    "created_at": (
                        row.created_at.isoformat()
                        if row.created_at else None
                    )
                }
                for row in result
            ]

        return {
            "success": True,
            "total": len(users),
            "users": users
        }

    except SQLAlchemyError:
        import logging
        logging.exception("Could not retrieve users")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve users."
        )


#==========================================
# DATABASE STATUS CHECK
#==========================================

@app.get("/api/db-status")
def database_status():

    if engine is None:
        return {
            "connected": False,
            "message": "DATABASE_URL is not configured."
        }

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "connected": True,
            "message": "PostgreSQL connection successful."
        }

    except SQLAlchemyError:
        return {
            "connected": False,
            "message": "Database connection failed."
        }
# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# SkillBridge Users Database Table
# ==========================================

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    login_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )



@app.post("/api/activity")
def record_activity(
    action: str,
    payload: dict = Depends(verify_access_token)
):
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    allowed_actions = {
        "resume_analyzer",
        "cover_letter",
        "learning_hub"
    }

    if action not in allowed_actions:
        raise HTTPException(
            status_code=400,
            detail="Invalid activity action."
        )

    try:
        user_id = int(payload["sub"])
        email = payload["email"]

        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO activity_logs
                    (user_id, email, action, created_at)
                    VALUES (:user_id, :email, :action, :created_at)
                """),
                {
                    "user_id": user_id,
                    "email": email,
                    "action": action,
                    "created_at": datetime.now(timezone.utc)
                }
            )

        return {
            "success": True,
            "message": "Activity recorded."
        }

    except HTTPException:
        raise
    except (SQLAlchemyError, ValueError, KeyError):
        import logging
        logging.exception("Could not record activity")
        raise HTTPException(
            status_code=500,
            detail="Could not record activity."
        )


@app.post("/api/db-create-tables")
def create_database_tables():
    if engine is None:
        return {
            "success": False,
            "message": "Database is not configured."
        }

    try:
        Base.metadata.create_all(bind=engine)
        return {
            "success": True,
            "message": "Users table created successfully."
        }
    except SQLAlchemyError:
        return {
            "success": False,
            "message": "Could not create database tables."
        }



class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str




@app.post("/api/login")
def login_user(user: UserLogin):
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    try:
        # Find user by email
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT id, name, email, password_hash
                    FROM users
                    WHERE email = :email
                """),
                {"email": user.email}
            ).mappings().first()

        if result is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        # Check password
        if result["password_hash"] == "NOT_SET":
            raise HTTPException(
                status_code=401,
                detail="Please register again with a password."
            )

        if not password_hash.verify(
            user.password,
            result["password_hash"]
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        # Save successful login history
        with engine.begin() as connection:
            connection.execute(
                text("""
                    INSERT INTO login_history
                    (user_id, email, login_at)
                    VALUES (:user_id, :email, :login_at)
                """),
                {
                    "user_id": result["id"],
                    "email": result["email"],
                    "login_at": datetime.now(timezone.utc)
                }
            )

        # Generate access token
        access_token = create_access_token(
            user_id=result["id"],
            email=result["email"]
        )

        return {
            "success": True,
            "message": "Login successful.",
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": result["id"],
                "name": result["name"],
                "email": result["email"]
            }
        }

    except HTTPException:
        raise

    except SQLAlchemyError:
        import logging
        logging.exception("Database error during login")
        raise HTTPException(
            status_code=500,
            detail="Login failed due to a server error."
        )



@app.get("/api/admin/login-history")
def get_login_history(
    admin: bool = Depends(verify_admin_key)
):
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text("""
                    SELECT id, user_id, email, login_at
                    FROM login_history
                    ORDER BY login_at DESC
                    LIMIT 200
                """)
            ).mappings().all()

        return {
            "success": True,
            "total": len(rows),
            "login_history": [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "login_at": (
                        row["login_at"].isoformat()
                        if row["login_at"] else None
                    )
                }
                for row in rows
            ]
        }

    except SQLAlchemyError:
        import logging
        logging.exception("Could not retrieve login history")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve login history."
        )



@app.get("/api/admin/activity-logs")
def get_activity_logs(
    admin: bool = Depends(verify_admin_key)
):
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    try:
        with engine.connect() as connection:
            rows = connection.execute(
                text("""
                    SELECT id, user_id, email, action, created_at
                    FROM activity_logs
                    ORDER BY created_at DESC
                    LIMIT 200
                """)
            ).mappings().all()

        return {
            "success": True,
            "total": len(rows),
            "activities": [
                {
                    "id": row["id"],
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "action": row["action"],
                    "created_at": (
                        row["created_at"].isoformat()
                        if row["created_at"] else None
                    )
                }
                for row in rows
            ]
        }

    except SQLAlchemyError:
        import logging
        logging.exception("Could not retrieve activity logs")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve activity logs."
        )


@app.post("/api/users")
def create_user(user: UserCreate):
    if engine is None:
        return {
            "success": False,
            "message": "Database is not configured."
        }

    try:
        with engine.begin() as connection:
            existing_user = connection.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user.email}
            ).first()

            if existing_user:
                return {
                    "success": False,
                    "message": "This email is already registered."
                }

            connection.execute(
                text("""
                    INSERT INTO users (name, email, password_hash, created_at)
                    VALUES (:name, :email, :password_hash, :created_at)
                """),
                {
                    "name": user.name,
                    "email": user.email,
                    "password_hash": password_hash.hash(user.password),
                    "created_at": datetime.now(timezone.utc)
                }
            )

        return {
            "success": True,
            "message": "User saved successfully."
        }

    except SQLAlchemyError:
        import logging
        logging.exception("Database error while saving user")
        return {
            "success": False,
            "message": "Could not save user."
        }


# =========================================================
# FIND FRONTEND FOLDER
# =========================================================

if getattr(sys, "frozen", False):
    # When running SkillBridge.exe
    BASE_DIR = Path(sys._MEIPASS)
else:
    # When running main.py
    BASE_DIR = Path(__file__).resolve().parents[1]


FRONTEND_DIR = BASE_DIR / "Fr"


# Check frontend folder
if not FRONTEND_DIR.exists():
    print("ERROR: Frontend folder not found:")
    print(FRONTEND_DIR)


# =========================================================
# SERVE FRONTEND FILES
# =========================================================

app.mount(
    "/assets",
    StaticFiles(directory=FRONTEND_DIR),
    name="assets"
)


from fastapi.responses import FileResponse

@app.get("/register.html")
def register_page():
    return FileResponse(FRONTEND_DIR / "register.html")


# =========================================================
# HOME PAGE
# =========================================================

@app.get("/")
def home():

    index_file = FRONTEND_DIR / "index.html"

    if index_file.exists():
        return FileResponse(index_file)

    return {
        "message": "Welcome to SkillBridge! 🚀"
    }


# =========================================================
# SUPPORT OLD RELATIVE CSS / JS PATHS
# =========================================================

@app.get("/style.css")
def style():

    css_file = FRONTEND_DIR / "style.css"

    if css_file.exists():
        return FileResponse(
            css_file,
            media_type="text/css"
        )

    return {
        "error": "style.css not found"
    }


@app.get("/script.js")
def script():

    js_file = FRONTEND_DIR / "script.js"

    if js_file.exists():
        return FileResponse(
            js_file,
            media_type="application/javascript"
        )

    return {
        "error": "script.js not found"
    }



@app.get("/manifest.json")
def manifest():

    manifest_file = FRONTEND_DIR / "manifest.json"

    if manifest_file.exists():
        return FileResponse(
            manifest_file,
            media_type="application/manifest+json"
        )

    return {
        "error": "manifest.json not found"
    }


@app.get("/service-worker.js")
def service_worker():

    sw_file = FRONTEND_DIR / "service-worker.js"

    if sw_file.exists():
        return FileResponse(
            sw_file,
            media_type="application/javascript"
        )

    return {
        "error": "service-worker.js not found"
    }


# =========================================================
# HELLO
# =========================================================

@app.get("/hello")
def hello():

    return {
        "message": "Build Your Career with SkillBridge! 🚀"
    }


# =========================================================
# RESUME ANALYZER
# =========================================================

@app.post("/api/analyze-resume")
async def analyze_resume(file: UploadFile = File(...)):

    try:

        # -------------------------------------------------
        # File name check
        # -------------------------------------------------

        if not file.filename:

            return {
                "error": "No file selected."
            }


        filename = file.filename.lower()


        # -------------------------------------------------
        # Read uploaded file
        # -------------------------------------------------

        content = await file.read()


        # -------------------------------------------------
        # PDF
        # -------------------------------------------------

        if filename.endswith(".pdf"):

            pdf_file = io.BytesIO(content)

            reader = PdfReader(pdf_file)

            text = ""

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:

                    text += page_text + "\n"


        # -------------------------------------------------
        # TXT
        # -------------------------------------------------

        elif filename.endswith(".txt"):

            text = content.decode(
                "utf-8",
                errors="ignore"
            )


        # -------------------------------------------------
        # Unsupported file
        # -------------------------------------------------

        else:

            return {
                "error": "Only PDF and TXT files are supported."
            }


        # -------------------------------------------------
        # Empty resume
        # -------------------------------------------------

        if not text.strip():

            return {
                "error": "Could not extract text from the resume."
            }


        text_lower = text.lower()


        # =================================================
        # SKILL DETECTION
        # =================================================

        skill_list = [

            # Programming
            "python",
            "java",
            "c",
            "c++",
            "c#",
            "javascript",
            "typescript",

            # Web Development
            "html",
            "css",
            "react",
            "node.js",
            "node",
            "angular",
            "django",
            "flask",
            "fastapi",

            # Database
            "sql",
            "mysql",
            "mongodb",
            "postgresql",
            "oracle",

            # Data / AI
            "data science",
            "data analytics",
            "data analysis",
            "machine learning",
            "deep learning",
            "artificial intelligence",
            "ai",

            # Python / ML Libraries
            "pandas",
            "numpy",
            "matplotlib",
            "scikit-learn",
            "opencv",
            "tensorflow",
            "pytorch",

            # Tools
            "git",
            "github",
            "docker",
            "kubernetes",

            # Cloud
            "aws",
            "azure",
            "google cloud",

            # Business / Data Tools
            "excel",
            "power bi",
            "tableau",

            # Other
            "linux",
            "ubuntu",
            "iot",
            "internet of things"
        ]


        detected_skills = []


        for skill in skill_list:

            if skill.lower() in text_lower:

                detected_skills.append(skill)


        # Remove duplicates

        detected_skills = list(
            dict.fromkeys(detected_skills)
        )


        # =================================================
        # EMAIL
        # =================================================

        email_found = bool(
            re.search(
                r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
                text
            )
        )


        # =================================================
        # PHONE
        # =================================================

        phone_found = bool(
            re.search(
                r"(\+91[\s-]?)?[6-9]\d{9}",
                text
            )
        )


        # =================================================
        # EDUCATION
        # =================================================

        education_keywords = [

            "education",
            "academic",
            "qualification",
            "bca",
            "mca",
            "b.tech",
            "btech",
            "m.tech",
            "mtech",
            "b.sc",
            "bsc",
            "m.sc",
            "msc",
            "degree",
            "university",
            "college",
            "school",
            "higher secondary",
            "secondary"
        ]


        education_found = any(
            word in text_lower
            for word in education_keywords
        )


        # =================================================
        # PROJECTS
        # =================================================

        project_keywords = [

            "project",
            "projects",
            "academic project",
            "personal project",
            "final year project"
        ]


        projects_found = any(
            word in text_lower
            for word in project_keywords
        )


        # =================================================
        # EXPERIENCE
        # =================================================

        experience_keywords = [

            "experience",
            "work experience",
            "professional experience",
            "internship",
            "intern",
            "employment",
            "worked at",
            "work history"
        ]


        experience_found = any(
            word in text_lower
            for word in experience_keywords
        )


        # =================================================
        # SKILLS SECTION
        # =================================================

        skills_section_keywords = [

            "skills",
            "technical skills",
            "key skills",
            "core skills",
            "skills & abilities"
        ]


        skills_section_found = any(
            word in text_lower
            for word in skills_section_keywords
        )


        # =================================================
        # PROFILE / SUMMARY
        # =================================================

        profile_keywords = [

            "profile",
            "professional summary",
            "career objective",
            "objective",
            "summary",
            "about me"
        ]


        profile_found = any(
            word in text_lower
            for word in profile_keywords
        )


        # =================================================
        # RESUME SCORE
        # =================================================

        score = 0


        if email_found:
            score += 10


        if phone_found:
            score += 10


        if education_found:
            score += 15


        if projects_found:
            score += 15


        if experience_found:
            score += 15


        if skills_section_found:
            score += 15


        if profile_found:
            score += 10


        if len(detected_skills) >= 5:

            score += 10

        elif len(detected_skills) >= 3:

            score += 7

        elif len(detected_skills) >= 1:

            score += 4


        if score > 100:

            score = 100


        # =================================================
        # SUGGESTIONS
        # =================================================

        suggestions = []


        if not email_found:

            suggestions.append(
                "Add a professional email address."
            )


        if not phone_found:

            suggestions.append(
                "Add your phone number."
            )


        if not profile_found:

            suggestions.append(
                "Add a short professional summary or career objective."
            )


        if not education_found:

            suggestions.append(
                "Add a clear Education section."
            )


        if not projects_found:

            suggestions.append(
                "Add academic or personal projects."
            )


        if not experience_found:

            suggestions.append(
                "Add internship or work experience if available."
            )


        if not skills_section_found:

            suggestions.append(
                "Add a clearly labelled Skills section."
            )


        if len(detected_skills) < 3:

            suggestions.append(
                "Add more relevant skills related to your target job."
            )


        if not suggestions:

            suggestions.append(
                "Your resume contains the major sections. "
                "Keep improving it with measurable achievements."
            )


        # =================================================
        # RESULT
        # =================================================

        return {

            "score": score,

            "skills": detected_skills,

            "sections": {

                "email": email_found,

                "phone": phone_found,

                "education": education_found,

                "projects": projects_found,

                "experience": experience_found,

                "skills": skills_section_found,

                "profile": profile_found
            },

            "suggestions": suggestions
        }


    except Exception as e:

        return {
            "error": f"Could not analyze resume: {str(e)}"
        }


# =========================================================
# COVER LETTER GENERATOR
# =========================================================

@app.post("/api/cover-letter")
async def generate_cover_letter(

    name: str = Form(...),

    role: str = Form(...),

    company: str = Form(...),

    skills: str = Form("")
):

    try:

        # -------------------------------------------------
        # Clean input
        # -------------------------------------------------

        name = name.strip()

        role = role.strip()

        company = company.strip()

        skills = skills.strip()


        # -------------------------------------------------
        # Default skills
        # -------------------------------------------------

        if not skills:

            skills = (
                "relevant technical and professional skills"
            )


        # -------------------------------------------------
        # Generate cover letter
        # -------------------------------------------------

        cover_letter = f"""Dear Hiring Manager,

I am writing to express my interest in the {role} position at {company}.

My name is {name}, and I am eager to build my professional career in this field. I believe that my academic background, willingness to learn, and relevant skills make me a suitable candidate for this opportunity.

My key skills include: {skills}.

I am a motivated and responsible individual who is willing to learn new technologies, work collaboratively, and contribute positively to your organization. I would appreciate the opportunity to apply my knowledge in a professional environment and further develop my skills.

I am particularly interested in the opportunity to work with {company} because it would allow me to learn, grow, and contribute to meaningful work.

Thank you for considering my application. I would be grateful for the opportunity to discuss my qualifications and suitability for the {role} position.

Sincerely,

{name}
"""


        return {
            "cover_letter": cover_letter
        }


    except Exception as e:

        return {
            "error": f"Could not generate cover letter: {str(e)}"
        }


# =========================================================
# START SERVER WHEN EXE IS RUN
# =========================================================

if __name__ == "__main__":

    import uvicorn


    def open_browser():

        time.sleep(2)

        webbrowser.open(
            "http://127.0.0.1:8000/"
        )


    # Open browser automatically

    threading.Thread(
        target=open_browser,
        daemon=True
    ).start()


    # Start FastAPI

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=False
    )
