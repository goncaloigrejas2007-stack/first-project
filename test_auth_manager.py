import pytest

import auth_manager


@pytest.fixture
def auth_db(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_DB_PATH", str(tmp_path / "users.db"))
    auth_manager.init_auth_db()
    return auth_manager


def test_registration_and_login_are_case_insensitive(auth_db):
    result = auth_db.register_user("alice", "Alice@example.com", "password123")

    assert result["success"]
    assert auth_db.login_user("ALICE", "password123")["success"]


def test_registration_rejects_invalid_values(auth_db):
    invalid_accounts = [
        ("", "person@example.com", "password123"),
        ("ab", "person@example.com", "password123"),
        ("person", "not-an-email", "password123"),
        ("person", "person@example.com", "short1"),
        ("person", "person@example.com", "password"),
        ("person", "person@example.com", "é" * 37 + "1"),
    ]

    for username, email, password in invalid_accounts:
        assert not auth_db.register_user(username, email, password)["success"]


@pytest.mark.parametrize(
    ("username", "email"),
    [
        ("ALICE", "other@example.com"),
        ("other", "ALICE@example.com"),
    ],
)
def test_registration_rejects_duplicate_username_or_email(auth_db, username, email):
    assert auth_db.register_user("alice", "alice@example.com", "password123")["success"]

    result = auth_db.register_user(username, email, "password456")

    assert not result["success"]
    assert "already in use" in result["message"]


def test_login_rejects_wrong_credentials(auth_db):
    auth_db.register_user("alice", "alice@example.com", "password123")

    assert not auth_db.login_user("alice", "wrongpassword1")["success"]
    assert not auth_db.login_user("unknown", "password123")["success"]


def test_user_settings_can_be_read_and_updated(auth_db):
    user_id = auth_db.register_user("alice", "alice@example.com", "password123")["user_id"]

    assert auth_db.get_user_settings(user_id) == {
        "theme": "light",
        "notifications_enabled": 1,
    }
    assert auth_db.update_user_settings(
        user_id,
        {"theme": "dark", "notifications_enabled": 0, "unknown": "ignored"},
    )
    assert auth_db.get_user_settings(user_id) == {
        "theme": "dark",
        "notifications_enabled": 0,
    }
