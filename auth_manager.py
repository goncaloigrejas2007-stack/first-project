import logging
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

import bcrypt

DB_PATH = Path(os.environ.get("AUTH_DB_PATH", Path(__file__).resolve().parent / "users.db"))
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt())


def connect():
    conn = sqlite3.connect(os.environ.get("AUTH_DB_PATH", DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def normalize_username(value: str) -> str:
    """Normalize username: strip whitespace"""
    return (value or "").strip()


def normalize_email(value: str) -> str:
    """Normalize email: strip whitespace and lowercase"""
    return (value or "").strip().lower()


def init_auth_db():
    """Initialize authentication database with proper constraints"""
    with closing(connect()) as conn:
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
                notifications_enabled INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users (LOWER(username))"
        )
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (LOWER(email))"
        )
        conn.commit()


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception:
        return False


def register_user(username: str, email: str, password: str) -> dict:
    """Register new user with validation"""
    username = normalize_username(username)
    email = normalize_email(email)
    password = password or ""

    if not username or not email or not password:
        return {"success": False, "message": "Username, email and password are required."}
    if len(username) < 3:
        return {"success": False, "message": "Username must be at least 3 characters."}
    password_bytes = password.encode()
    if (
        len(password) < 8
        or not any(character.isalpha() for character in password)
        or not any(character.isdigit() for character in password)
    ):
        return {
            "success": False,
            "message": "Password must be at least 8 characters and include a letter and a digit.",
        }
    if len(password_bytes) > 72:
        return {"success": False, "message": "Password must be no more than 72 bytes."}
    if not EMAIL_PATTERN.fullmatch(email):
        return {"success": False, "message": "Invalid email format."}

    try:
        with closing(connect()) as conn:
            password_hash = hash_password(password)
            cursor = conn.execute(
                """
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (username, email, password_hash, datetime.now().isoformat()),
            )
            user_id = cursor.lastrowid
            conn.execute("INSERT INTO user_settings (user_id) VALUES (?)", (user_id,))
            conn.commit()
        return {
            "success": True,
            "message": "Account created successfully! Please log in.",
            "user_id": user_id,
        }
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username or email already in use."}
    except Exception:
        logging.exception("User registration failed")
        return {"success": False, "message": "Registration failed. Please try again."}


def login_user(username: str, password: str) -> dict:
    """Authenticate user with case-insensitive username"""
    username = normalize_username(username)
    password = password or ""

    if not username or not password:
        return {"success": False, "message": "Username and password are required."}

    try:
        with closing(connect()) as conn:
            result = conn.execute(
                "SELECT id, password_hash, email, username FROM users WHERE LOWER(username) = LOWER(?)",
                (username,),
            ).fetchone()

            if result is None:
                verify_password(password, DUMMY_PASSWORD_HASH.decode())
                return {"success": False, "message": "Invalid username or password."}

            user_id, password_hash, email, actual_username = result
            if not verify_password(password, password_hash):
                return {"success": False, "message": "Invalid username or password."}

            conn.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.now().isoformat(), user_id),
            )
            conn.commit()
        return {
            "success": True,
            "message": "Login successful!",
            "user_id": user_id,
            "username": actual_username,
            "email": email,
        }
    except Exception:
        logging.exception("User login failed")
        return {"success": False, "message": "Login failed. Please try again."}


def get_user_settings(user_id: int) -> dict:
    """Get settings, creating defaults for accounts without a settings row."""
    defaults = {"theme": "light", "notifications_enabled": 1}
    try:
        with closing(connect()) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute(
                "INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)",
                (int(user_id),),
            )
            conn.commit()
            row = conn.execute(
                "SELECT theme, notifications_enabled FROM user_settings WHERE user_id = ?",
                (int(user_id),),
            ).fetchone()
            return dict(row) if row else defaults
    except Exception:
        logging.exception("Could not load user settings")
        return defaults


def update_user_settings(user_id: int, settings: dict) -> bool:
    """Update user settings"""
    columns = {"theme": "theme", "notifications_enabled": "notifications_enabled"}
    try:
        with closing(connect()) as conn:
            for key, value in settings.items():
                column = columns.get(key)
                if column is None:
                    continue
                if key == "theme" and value not in ("light", "dark"):
                    continue
                conn.execute(
                    f"UPDATE user_settings SET {column} = ? WHERE user_id = ?",
                    (value, int(user_id)),
                )
            conn.commit()
        return True
    except Exception:
        logging.exception("Could not update user settings")
        return False
