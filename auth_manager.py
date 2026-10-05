import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path

import bcrypt

logger = logging.getLogger(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
INVALID_LOGIN = "Invalid username or password."
GENERIC_ERROR = "Something went wrong. Please try again."
DB_PATH = Path(__file__).resolve().parent / "users.db"


def normalize_username(value: str) -> str:
    """Normalize username: strip whitespace"""
    return (value or "").strip()


def normalize_email(value: str) -> str:
    """Normalize email: strip whitespace and lowercase"""
    return (value or "").strip().lower()


def init_auth_db():
    """Initialize authentication database with proper constraints"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            theme TEXT DEFAULT 'light',
            llm_model TEXT DEFAULT 'groq',
            notifications_enabled INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )
    # Create case-insensitive indexes for username and email
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (LOWER(username))"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (LOWER(email))"
    )
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


def validate_password(password: str):
    """Return an error message if the password is weak, otherwise None"""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if len(password.encode()) > 72:
        return "Password must be at most 72 bytes."
    if not (re.search(r"[A-Za-z]", password) and re.search(r"\d", password)):
        return "Password must contain at least one letter and one number."
    return None


DUMMY_HASH = hash_password("dummy-password-for-timing")


def register_user(username: str, email: str, password: str) -> dict:
    """Register new user with validation"""
    username = normalize_username(username)
    email = normalize_email(email)
    password = (password or "").strip()

    # Validation
    if not username or not email or not password:
        return {"success": False, "message": "Username, email and password are required."}
    
    if len(username) < 3:
        return {"success": False, "message": "Username must be at least 3 characters."}

    password_error = validate_password(password)
    if password_error:
        return {"success": False, "message": password_error}

    if not EMAIL_RE.match(email):
        return {"success": False, "message": "Invalid email format."}

    try:
        conn = sqlite3.connect(DB_PATH)
        password_hash = hash_password(password)

        cursor = conn.execute(
            """
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, datetime.now().isoformat()),
        )

        user_id = cursor.lastrowid

        # Add default settings
        conn.execute(
            "INSERT INTO user_settings (user_id) VALUES (?)",
            (user_id,),
        )

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Account created successfully! Please log in.",
            "user_id": user_id,
        }
    except sqlite3.IntegrityError as e:
        conn.close()
        return {"success": False, "message": "Username or email is already in use."}
    except Exception:
        logger.exception("Registration failed")
        return {"success": False, "message": GENERIC_ERROR}


def login_user(username: str, password: str) -> dict:
    """Authenticate user with case-insensitive username"""
    username = normalize_username(username)
    password = (password or "").strip()

    if not username or not password:
        return {"success": False, "message": "Username and password are required."}

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Case-insensitive username search
        cursor.execute(
            "SELECT id, password_hash, email, username FROM users WHERE LOWER(username) = LOWER(?)",
            (username,),
        )

        result = cursor.fetchone()

        if result is None:
            conn.close()
            verify_password(password, DUMMY_HASH)
            return {"success": False, "message": INVALID_LOGIN}

        user_id, password_hash, email, actual_username = result

        if verify_password(password, password_hash):
            # Update last login
            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user_id),
            )
            conn.commit()
            conn.close()

            return {
                "success": True,
                "message": "Login successful!",
                "user_id": user_id,
                "username": actual_username,
                "email": email,
            }
        else:
            conn.close()
            return {"success": False, "message": INVALID_LOGIN}

    except Exception:
        logger.exception("Login failed")
        return {"success": False, "message": GENERIC_ERROR}


def get_user_by_id(user_id: int) -> dict:
    """Get user info by ID"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, email, created_at, last_login FROM users WHERE id = ?",
            (user_id,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "id": result[0],
                "username": result[1],
                "email": result[2],
                "created_at": result[3],
                "last_login": result[4],
            }
        return None
    except Exception:
        return None


def get_user_settings(user_id: int) -> dict:
    """Get user settings"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT theme, llm_model, notifications_enabled FROM user_settings WHERE user_id = ?",
            (user_id,),
        )

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                "theme": result[0],
                "llm_model": result[1],
                "notifications_enabled": result[2],
            }
        return {"theme": "light", "llm_model": "groq", "notifications_enabled": 1}
    except Exception:
        return {"theme": "light", "llm_model": "groq", "notifications_enabled": 1}


def update_user_settings(user_id: int, settings: dict) -> bool:
    """Update user settings"""
    try:
        conn = sqlite3.connect(DB_PATH)

        for key, value in settings.items():
            if key in ["theme", "llm_model", "notifications_enabled"]:
                conn.execute(
                    f"UPDATE user_settings SET {key} = ? WHERE user_id = ?",
                    (value, user_id),
                )

        conn.commit()
        conn.close()
        return True
    except Exception:
        return False
