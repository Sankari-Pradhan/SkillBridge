from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from pypdf import PdfReader

from pathlib import Path

import io
import re
import sys
import threading
import time
import webbrowser


# =========================================================
# SKILLBRIDGE
# =========================================================

app = FastAPI(
    title="SkillBridge",
    description="Your Personal Career and Learning Assistant",
    version="1.0.0"
)


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