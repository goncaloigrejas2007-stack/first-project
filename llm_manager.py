import sqlite3
from datetime import datetime
from pathlib import Path

import bcrypt

DB_PATH = Path(__file__).resolve().parent / "users.db"


def normalize_username(value: str) -> str:
    return (value or "").strip()


def normalize_email(value: str) -> str:
    return (value or "").strip().lower()


def init_auth_db():
    """Initialize authentication database"""
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
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_ci ON users (LOWER(username))"
    )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_ci ON users (LOWER(email))"
    )
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def register_user(username: str, email: str, password: str) -> dict:
    """Register new user"""
    username = normalize_username(username)
    email = normalize_email(email)
    password = (password or "").strip()

    if not username or not email or not password:
        return {"success": False, "message": "Username, email and password are required."}
    if len(password) < 6:
        return {"success": False, "message": "Password must be at least 6 characters long."}

    try:
        conn = sqlite3.connect(DB_PATH)
        password_hash = hash_password(password)

        conn.execute(
            """
            INSERT INTO users (username, email, password_hash, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, datetime.now().isoformat()),
        )

        user_id = conn.lastrowid
        conn.execute(
            "INSERT INTO user_settings (user_id) VALUES (?)",
            (user_id,),
        )

        conn.commit()
        conn.close()
        return {"success": True, "message": "User registered successfully!", "user_id": user_id}
    except sqlite3.IntegrityError as e:
        if "username" in str(e).lower():
            return {"success": False, "message": "Username already exists"}
        if "email" in str(e).lower():
            return {"success": False, "message": "Email already exists"}
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


def login_user(username: str, password: str) -> dict:
    """Authenticate user"""
    username = normalize_username(username)
    password = (password or "").strip()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, password_hash, email FROM users WHERE LOWER(username) = LOWER(?)",
            (username,),
        )

        result = cursor.fetchone()
        if result is None:
            conn.close()
            return {"success": False, "message": "User not found"}

        user_id, password_hash, email = result

        if verify_password(password, password_hash):
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
                "username": username,
                "email": email,
            }

        conn.close()
        return {"success": False, "message": "Invalid password"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}


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
