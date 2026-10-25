from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles



from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone, timedelta
from pypdf import PdfReader

from sqlalchemy import Text

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
import hashlib
import json
import urllib.request
import urllib.error
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
def list_users(admin: bool = Depends(verify_admin_key)):
    if engine is None:
        raise HTTPException(status_code=503, detail="Database is not configured.")
    try:
        ensure_admin_user_columns()
        with engine.connect() as connection:
            rows = connection.execute(text("""
                SELECT id, name, email, created_at, is_active
                FROM users
                ORDER BY id DESC
            """)).mappings().all()
        users = [{
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "is_active": row["is_active"]
        } for row in rows]
        return {"success": True, "total": len(users), "users": users}
    except HTTPException:
        raise
    except SQLAlchemyError:
        import logging
        logging.exception("Could not retrieve users")
        raise HTTPException(status_code=500, detail="Could not retrieve users.")


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

    # NEW: Store activity details
    details = Column(Text, nullable=True)

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
    "home",
    "learning_hub",
    "career_opportunities",
    "create_resume",
    "profile"
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

        # Add details column to existing activity_logs table
        with engine.begin() as conn:
            conn.execute(text("""
                ALTER TABLE activity_logs
                ADD COLUMN IF NOT EXISTS details TEXT
            """))

        return {
            "success": True,
            "message": "Database tables and activity details column created successfully."
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
        # Ensure existing databases have the account-status column.
        with engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE users
                ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
            """))
        # Find user by email
        with engine.connect() as connection:
            result = connection.execute(
                text("""
                    SELECT id, name, email, password_hash, is_active
                    FROM users
                    WHERE lower(email) = lower(:email)
                """),
                {"email": user.email}
            ).mappings().first()

        if result is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        # Deactivated accounts cannot log in.
        if result.get("is_active") is False:
            raise HTTPException(status_code=403, detail="This account has been deactivated. Contact the administrator.")

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



@app.post("/api/admin/fix-activity-details")
def fix_activity_details(
    admin: bool = Depends(verify_admin_key)
):
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    try:
        with engine.begin() as connection:
            connection.execute(text("""
                ALTER TABLE activity_logs
                ADD COLUMN IF NOT EXISTS details TEXT
            """))

        return {
            "success": True,
            "message": "Activity details column is ready."
        }

    except SQLAlchemyError:
        import logging
        logging.exception("Could not add activity details column")
        raise HTTPException(
            status_code=500,
            detail="Could not fix activity details column."
        )

# =========================================================
# EMAIL OTP REGISTRATION (Mailjet)
# =========================================================

class RegistrationOTPRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class RegistrationOTPVerify(BaseModel):
    email: EmailStr
    otp: str



# ================= FORGOT PASSWORD OTP =================

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str


def ensure_forgot_password_table():
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS forgot_password_otps (
                email VARCHAR(255) PRIMARY KEY,
                otp_hash VARCHAR(64) NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_sent_at TIMESTAMPTZ NOT NULL
            )
        """))


@app.post("/api/forgot-password/send-otp")
def send_forgot_password_otp(data: ForgotPasswordRequest):
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    email = str(data.email).strip().lower()
    ensure_forgot_password_table()

    with engine.begin() as connection:
        user = connection.execute(
            text("""
                SELECT id
                FROM users
                WHERE lower(email) = :email
            """),
            {"email": email}
        ).first()

        if not user:
            # Avoid revealing whether an account exists.
            return {
                "success": True,
                "message": "If the account exists, an OTP may be sent."
            }

        previous = connection.execute(
            text("""
                SELECT last_sent_at
                FROM forgot_password_otps
                WHERE email = :email
            """),
            {"email": email}
        ).mappings().first()

        now = datetime.now(timezone.utc)

        if previous and (
            now - previous["last_sent_at"]
        ).total_seconds() < 60:
            raise HTTPException(
                status_code=429,
                detail="Please wait 60 seconds before requesting another OTP."
            )

    otp = f"{secrets.randbelow(1_000_000):06d}"
    otp_digest = hashlib.sha256(otp.encode("utf-8")).hexdigest()

    # Uses the Mailjet helper already present in main.py.
    send_mailjet_otp(email, otp)

    now = datetime.now(timezone.utc)

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO forgot_password_otps
                    (email, otp_hash, expires_at, attempts, last_sent_at)
                VALUES
                    (:email, :otp_hash, :expires_at, 0, :last_sent_at)
                ON CONFLICT (email) DO UPDATE SET
                    otp_hash = EXCLUDED.otp_hash,
                    expires_at = EXCLUDED.expires_at,
                    attempts = 0,
                    last_sent_at = EXCLUDED.last_sent_at
            """),
            {
                "email": email,
                "otp_hash": otp_digest,
                "expires_at": now + timedelta(minutes=10),
                "last_sent_at": now
            }
        )

    return {
        "success": True,
        "message": "If the account exists, an OTP may be sent."
    }


@app.post("/api/forgot-password/reset")
def reset_forgotten_password(data: ResetPasswordRequest):
    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    email = str(data.email).strip().lower()
    otp = data.otp.strip()

    if not otp.isdigit() or len(otp) != 6:
        raise HTTPException(status_code=400, detail="Invalid OTP.")

    if len(data.new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long."
        )

    ensure_forgot_password_table()

    now = datetime.now(timezone.utc)
    otp_digest = hashlib.sha256(otp.encode("utf-8")).hexdigest()

    with engine.begin() as connection:
        record = connection.execute(
            text("""
                SELECT otp_hash, expires_at, attempts
                FROM forgot_password_otps
                WHERE email = :email
                FOR UPDATE
            """),
            {"email": email}
        ).mappings().first()

        if not record:
            raise HTTPException(
                status_code=400,
                detail="Request a new OTP first."
            )

        if record["expires_at"] <= now:
            connection.execute(
                text("DELETE FROM forgot_password_otps WHERE email = :email"),
                {"email": email}
            )
            raise HTTPException(
                status_code=400,
                detail="OTP expired. Please request a new one."
            )

        if record["attempts"] >= 5:
            raise HTTPException(
                status_code=429,
                detail="Too many attempts. Request a new OTP."
            )

        if not secrets.compare_digest(record["otp_hash"], otp_digest):
            connection.execute(
                text("""
                    UPDATE forgot_password_otps
                    SET attempts = attempts + 1
                    WHERE email = :email
                """),
                {"email": email}
            )
            raise HTTPException(status_code=400, detail="Invalid OTP.")

        result = connection.execute(
            text("""
                UPDATE users
                SET password_hash = :password_hash
                WHERE lower(email) = :email
            """),
            {
                "email": email,
                "password_hash": password_hash.hash(data.new_password)
            }
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=400, detail="Account not found.")

        connection.execute(
            text("DELETE FROM forgot_password_otps WHERE email = :email"),
            {"email": email}
        )

    return {
        "success": True,
        "message": "Password reset successfully. Please log in."
    }



def ensure_registration_otp_table():
    """Create a table for pending registrations; OTPs are stored hashed."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Database is not configured.")
    with engine.begin() as connection:
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS registration_otps (
                email VARCHAR(255) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                otp_hash VARCHAR(64) NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_sent_at TIMESTAMPTZ NOT NULL
            )
        """))


def send_mailjet_otp(recipient_email: str, otp: str):
    api_key = os.getenv("MAILJET_API_KEY")
    secret_key = os.getenv("MAILJET_SECRET_KEY")
    sender_email = os.getenv("MAILJET_SENDER_EMAIL")
    if not api_key or not secret_key or not sender_email:
        raise HTTPException(status_code=503, detail="Email service is not configured.")

    payload = {
        "Messages": [{
            "From": {"Email": sender_email, "Name": "SkillBridge"},
            "To": [{"Email": recipient_email}],
            "Subject": "Your SkillBridge registration OTP",
            "TextPart": f"Your SkillBridge verification code is {otp}. It expires in 10 minutes. If you did not request this code, ignore this email.",
            "HTMLPart": f"<p>Your SkillBridge verification code is:</p><h2>{otp}</h2><p>This code expires in 10 minutes. If you did not request it, ignore this email.</p>"
        }]
    }
    request = urllib.request.Request(
        "https://api.mailjet.com/v3.1/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    import base64
    credentials = base64.b64encode(f"{api_key}:{secret_key}".encode("utf-8")).decode("ascii")
    request.add_header("Authorization", f"Basic {credentials}")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response_body = json.loads(response.read().decode("utf-8"))
            messages = response_body.get("Messages", [])
            if not messages or messages[0].get("Status") != "success":
                raise HTTPException(status_code=502, detail="Email provider did not accept the OTP email.")
    except urllib.error.HTTPError as exc:
        # Do not expose provider credentials or full provider response to the client.
        import logging
        logging.error("Mailjet rejected OTP email; HTTP status %s", exc.code)
        raise HTTPException(status_code=502, detail="Could not send verification email. Check Mailjet sender and API settings.")
    except (urllib.error.URLError, TimeoutError):
        raise HTTPException(status_code=502, detail="Email service is temporarily unavailable.")



@app.post("/api/register/send-otp")
def send_registration_otp(user: RegistrationOTPRequest):
    """Send an OTP without creating the account yet."""

    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    name = user.name.strip()
    email = str(user.email).strip().lower()

    if not name or len(name) > 100:
        raise HTTPException(
            status_code=400,
            detail="Enter a valid name (maximum 100 characters)."
        )

    if len(user.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long."
        )

    ensure_registration_otp_table()

    with engine.begin() as connection:
        existing = connection.execute(
            text("""
                SELECT id
                FROM users
                WHERE lower(email) = :email
            """),
            {"email": email}
        ).first()

        if existing:
            raise HTTPException(
                status_code=409,
                detail="This email is already registered. Please log in."
            )

        pending = connection.execute(
            text("""
                SELECT last_sent_at
                FROM registration_otps
                WHERE email = :email
            """),
            {"email": email}
        ).mappings().first()

        now = datetime.now(timezone.utc)

        if pending and (
            now - pending["last_sent_at"]
        ).total_seconds() < 60:
            raise HTTPException(
                status_code=429,
                detail="Please wait 60 seconds before requesting another OTP."
            )

    otp = f"{secrets.randbelow(1_000_000):06d}"
    otp_hash = hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()

    # Send the email before saving the pending registration.
    send_mailjet_otp(email, otp)

    now = datetime.now(timezone.utc)

    with engine.begin() as connection:
        connection.execute(
            text("""
                INSERT INTO registration_otps (
                    email,
                    name,
                    password_hash,
                    otp_hash,
                    expires_at,
                    attempts,
                    last_sent_at
                )
                VALUES (
                    :email,
                    :name,
                    :password_hash,
                    :otp_hash,
                    :expires_at,
                    0,
                    :last_sent_at
                )
                ON CONFLICT (email) DO UPDATE SET
                    name = EXCLUDED.name,
                    password_hash = EXCLUDED.password_hash,
                    otp_hash = EXCLUDED.otp_hash,
                    expires_at = EXCLUDED.expires_at,
                    attempts = 0,
                    last_sent_at = EXCLUDED.last_sent_at
            """),
            {
                "email": email,
                "name": name,
                "password_hash": password_hash.hash(user.password),
                "otp_hash": otp_hash,
                "expires_at": now + timedelta(minutes=10),
                "last_sent_at": now
            }
        )

    return {
        "success": True,
        "message": "OTP sent. Check your email and verify within 10 minutes."
    }


@app.post("/api/register/verify-otp")
def verify_registration_otp(data: RegistrationOTPVerify):
    """Create the account only after successful OTP verification."""

    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    email = str(data.email).strip().lower()
    otp = data.otp.strip()

    if not re.fullmatch(r"\d{6}", otp):
        raise HTTPException(
            status_code=400,
            detail="Enter the 6-digit OTP."
        )

    ensure_registration_otp_table()

    otp_hash = hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()

    now = datetime.now(timezone.utc)

    with engine.begin() as connection:
        pending = connection.execute(
            text("""
                SELECT
                    name,
                    password_hash,
                    otp_hash,
                    expires_at,
                    attempts
                FROM registration_otps
                WHERE email = :email
                FOR UPDATE
            """),
            {"email": email}
        ).mappings().first()

        if not pending:
            raise HTTPException(
                status_code=400,
                detail="No pending registration found. Request a new OTP."
            )

        if pending["expires_at"] <= now:
            connection.execute(
                text("""
                    DELETE FROM registration_otps
                    WHERE email = :email
                """),
                {"email": email}
            )
            raise HTTPException(
                status_code=400,
                detail="OTP expired. Please request a new OTP."
            )

        if pending["attempts"] >= 5:
            connection.execute(
                text("""
                    DELETE FROM registration_otps
                    WHERE email = :email
                """),
                {"email": email}
            )
            raise HTTPException(
                status_code=429,
                detail="Too many incorrect attempts. Request a new OTP."
            )

        if not secrets.compare_digest(
            pending["otp_hash"], otp_hash
        ):
            connection.execute(
                text("""
                    UPDATE registration_otps
                    SET attempts = attempts + 1
                    WHERE email = :email
                """),
                {"email": email}
            )
            raise HTTPException(
                status_code=400,
                detail="Incorrect OTP. Please try again."
            )

        existing = connection.execute(
            text("""
                SELECT id
                FROM users
                WHERE lower(email) = :email
            """),
            {"email": email}
        ).first()

        if existing:
            connection.execute(
                text("""
                    DELETE FROM registration_otps
                    WHERE email = :email
                """),
                {"email": email}
            )
            raise HTTPException(
                status_code=409,
                detail="This email is already registered. Please log in."
            )

        connection.execute(
            text("""
                INSERT INTO users (
                    name,
                    email,
                    password_hash,
                    created_at
                )
                VALUES (
                    :name,
                    :email,
                    :password_hash,
                    :created_at
                )
            """),
            {
                "name": pending["name"],
                "email": email,
                "password_hash": pending["password_hash"],
                "created_at": now
            }
        )

        connection.execute(
            text("""
                DELETE FROM registration_otps
                WHERE email = :email
            """),
            {"email": email}
        )

    return {
        "success": True,
        "message": "Email verified and account created successfully. You can now log in."
    }


@app.post("/api/users")
def create_user(user: UserCreate):
    """Prevent account creation without OTP verification."""

    raise HTTPException(
        status_code=410,
        detail=(
            "Direct registration is disabled. Use "
            "/api/register/send-otp then "
            "/api/register/verify-otp."
        )
    )





# =========================================================
# ADMIN ACCOUNT MANAGEMENT
# =========================================================

class AdminUserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None

def ensure_admin_user_columns():
    """Add account status column safely for existing PostgreSQL databases."""
    if engine is None:
        raise HTTPException(status_code=503, detail="Database is not configured.")
    with engine.begin() as connection:
        connection.execute(text("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
        """))

@app.get("/api/admin/account-history")
def get_admin_account_history(
    admin: bool = Depends(verify_admin_key)
):
    """Return login and page activity history for the admin dashboard."""

    if engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured."
        )

    try:
        ensure_admin_user_columns()

        with engine.connect() as connection:

            logins = connection.execute(text("""
                SELECT
                    id,
                    user_id,
                    email,
                    login_at AS event_at,
                    'login' AS event_type,
                    'Successful login' AS details
                FROM login_history
                ORDER BY login_at DESC
                LIMIT 200
            """)).mappings().all()

            activities = connection.execute(text("""
                SELECT
                    id,
                    user_id,
                    email,
                    created_at AS event_at,
                    'activity' AS event_type,
                    action AS details
                FROM activity_logs
                WHERE action IN (
                    'home',
                    'learning_hub',
                    'career_opportunities',
                    'create_resume',
                    'profile',
                    'resume_analyzer',
                    'cover_letter'
                )
                ORDER BY created_at DESC
                LIMIT 200
            """)).mappings().all()

        events = []

        page_names = {
            "home": "🏠 Home",
            "learning_hub": "📚 Learning Hub",
            "career_opportunities": "💼 Career Opportunities",
            "create_resume": "📄 Create Resume",
            "profile": "👤 Profile",
            "resume_analyzer": "Resume Analyzer",
            "cover_letter": "Cover Letter Generator"
        }

        for row in logins:
            events.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "email": row["email"],
                "event_at": (
                    row["event_at"].isoformat()
                    if row["event_at"] else None
                ),
                "event_type": "Login",
                "details": "Successful login"
            })

        for row in activities:
            action = row["details"]

            events.append({
                "id": row["id"],
                "user_id": row["user_id"],
                "email": row["email"],
                "event_at": (
                    row["event_at"].isoformat()
                    if row["event_at"] else None
                ),
                "event_type": "Page Activity",
                "details": page_names.get(action, action)
            })

        events.sort(
            key=lambda item: item["event_at"] or "",
            reverse=True
        )

        events = events[:300]

        return {
            "success": True,
            "total": len(events),
            "history": events
        }

    except SQLAlchemyError:
        import logging

        logging.exception(
            "Could not retrieve admin account history"
        )

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve account history."
        )

@app.patch("/api/admin/users/{user_id}")
def admin_update_user(
    user_id: int,
    data: AdminUserUpdate,
    admin: bool = Depends(verify_admin_key)
):
    if engine is None:
        raise HTTPException(status_code=503, detail="Database is not configured.")
    if data.name is None and data.email is None:
        raise HTTPException(status_code=400, detail="Provide a name or email to update.")
    try:
        ensure_admin_user_columns()
        updates = {}
        if data.name is not None:
            name = data.name.strip()
            if not name:
                raise HTTPException(status_code=400, detail="Name cannot be empty.")
            if len(name) > 100:
                raise HTTPException(status_code=400, detail="Name must be 100 characters or fewer.")
            updates["name"] = name
        if data.email is not None:
            updates["email"] = str(data.email).strip().lower()
        with engine.begin() as connection:
            current = connection.execute(
                text("SELECT id FROM users WHERE id = :id"), {"id": user_id}
            ).first()
            if not current:
                raise HTTPException(status_code=404, detail="User not found.")
            if "email" in updates:
                duplicate = connection.execute(text(
                    "SELECT id FROM users WHERE email = :email AND id <> :id"
                ), {"email": updates["email"], "id": user_id}).first()
                if duplicate:
                    raise HTTPException(status_code=409, detail="Email is already used by another account.")
            set_clause = ", ".join(f"{column} = :{column}" for column in updates)
            updates["id"] = user_id
            connection.execute(text(f"UPDATE users SET {set_clause} WHERE id = :id"), updates)
            row = connection.execute(text(
                "SELECT id, name, email, created_at, is_active FROM users WHERE id = :id"
            ), {"id": user_id}).mappings().first()
        return {"success": True, "message": "User updated.", "user": {
            "id": row["id"], "name": row["name"], "email": row["email"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "is_active": row["is_active"]
        }}
    except HTTPException:
        raise
    except SQLAlchemyError:
        import logging
        logging.exception("Could not update user")
        raise HTTPException(status_code=500, detail="Could not update user.")

@app.patch("/api/admin/users/{user_id}/status")
def admin_set_user_status(
    user_id: int,
    is_active: bool,
    admin: bool = Depends(verify_admin_key)
):
    if engine is None:
        raise HTTPException(status_code=503, detail="Database is not configured.")
    try:
        ensure_admin_user_columns()
        with engine.begin() as connection:
            result = connection.execute(text("""
                UPDATE users SET is_active = :is_active
                WHERE id = :id
            """), {"is_active": is_active, "id": user_id})
            if result.rowcount == 0:
                raise HTTPException(status_code=404, detail="User not found.")
        return {"success": True, "message": "Account activated." if is_active else "Account deactivated."}
    except HTTPException:
        raise
    except SQLAlchemyError:
        import logging
        logging.exception("Could not change account status")
        raise HTTPException(status_code=500, detail="Could not change account status.")

@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: int, admin: bool = Depends(verify_admin_key)):
    if engine is None:
        raise HTTPException(status_code=503, detail="Database is not configured.")
    try:
        ensure_admin_user_columns()
        with engine.begin() as connection:
            row = connection.execute(text(
                "SELECT id, email FROM users WHERE id = :id"
            ), {"id": user_id}).mappings().first()
            if not row:
                raise HTTPException(status_code=404, detail="User not found.")
            # Keep audit/history records, but remove the account itself.
            connection.execute(text("DELETE FROM users WHERE id = :id"), {"id": user_id})
        return {"success": True, "message": "User account deleted. Existing history records were retained."}
    except HTTPException:
        raise
    except SQLAlchemyError:
        import logging
        logging.exception("Could not delete user")
        raise HTTPException(status_code=500, detail="Could not delete user.")


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

@app.get("/admin.html")
def admin_page():
    return FileResponse(FRONTEND_DIR / "admin.html")


@app.get("/register.html")
def register_page():
    return FileResponse(FRONTEND_DIR / "register.html")


@app.get("/forgot-password.html")
def forgot_password_page():
    page = FRONTEND_DIR / "forgot-password.html"
    if not page.is_file():
        raise HTTPException(status_code=404, detail="Forgot Password page not found.")
    return FileResponse(page)


# Support links using the /Fr/ prefix
@app.get("/Fr/index.html")
def frontend_index_page():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/Fr/register.html")
def frontend_register_page():
    return FileResponse(FRONTEND_DIR / "register.html")


@app.get("/Fr/forgot-password.html")
def frontend_forgot_password_page():
    page = FRONTEND_DIR / "forgot-password.html"
    if not page.is_file():
        raise HTTPException(status_code=404, detail="Forgot Password page not found.")
    return FileResponse(page)



# =========================================================
# HOME PAGE
# =========================================================

@app.get("/")
def home():

    index_file = FRONTEND_DIR / "index.html"

    print("FRONTEND_DIR:", FRONTEND_DIR)
    print("INDEX EXISTS:", index_file.exists())

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


  
        # Read uploaded file
        content = await file.read()

        # PDF
        if filename.endswith(".pdf"):
            try:
                pdf_file = io.BytesIO(content)
                reader = PdfReader(pdf_file)

                text = ""
                for page in reader.pages:
                    text += (page.extract_text() or "") + "\n"

            except Exception:
                raise HTTPException(
                    status_code=400,
                    detail="Could not read this PDF file. Please upload a valid PDF."
                )

        # TXT
        elif filename.endswith(".txt"):
            text = content.decode("utf-8", errors="ignore")

        # Unsupported file
        else:
            raise HTTPException(
                status_code=400,
                detail="Only PDF and TXT files are supported."
            )

        # Empty resume
        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from the resume. Try a text-based PDF or TXT file."
            )


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
