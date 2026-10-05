import importlib
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import auth_manager  # noqa: E402
import finance_utils  # noqa: E402
import llm_manager  # noqa: E402


def test_llm_manager_exposes_getter(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setattr("dotenv.load_dotenv", lambda *a, **k: False)
    assert llm_manager.get_llm_manager() is None
    monkeypatch.setenv("GROQ_API_KEY", "abc")
    assert llm_manager.get_llm_manager() is not None


def test_filter_month_separates_years():
    df = pd.DataFrame({"date": pd.to_datetime(["2024-03-05", "2025-03-05", "2025-04-01"]), "amount": [1, 2, 3]})
    result = finance_utils.filter_month(df, 2025, 3)
    assert result["amount"].tolist() == [2]
    assert finance_utils.filter_month(df.iloc[0:0], 2025, 3).empty


@pytest.mark.parametrize("value", [0, -5, "x", float("nan"), float("inf")])
def test_validate_positive_rejects(value):
    assert finance_utils.validate_positive(value)


def test_validate_positive_accepts():
    assert finance_utils.validate_positive(0.01) is None


def test_escape_html():
    assert "<script>" not in finance_utils.escape_html("<script>")


def test_category_validation():
    assert finance_utils.validate_category_name("  ")
    assert finance_utils.validate_category_name("income")
    assert finance_utils.validate_category_name("Pets") is None


@pytest.fixture
def auth_db(tmp_path, monkeypatch):
    monkeypatch.setattr(auth_manager, "DB_PATH", tmp_path / "users.db")
    auth_manager.init_auth_db()


def test_register_and_login(auth_db):
    assert not auth_manager.register_user("alice", "a@b.co", "short1")["success"]
    assert not auth_manager.register_user("alice", "a@b.co", "onlyletters")["success"]
    result = auth_manager.register_user("alice", "a@b.co", "password123")
    assert result["success"] and result["user_id"]
    assert not auth_manager.register_user("ALICE", "x@y.co", "password123")["success"]
    assert auth_manager.login_user("Alice", "password123")["success"]
    wrong_pw = auth_manager.login_user("alice", "wrongpass1")
    unknown = auth_manager.login_user("nobody", "wrongpass1")
    assert wrong_pw["message"] == unknown["message"]


def test_app_imports_resolve():
    source = (Path(__file__).resolve().parent.parent / "streamlit_app.py").read_text()
    assert "from llm_manager import get_llm_manager" in source
    assert callable(importlib.import_module("llm_manager").get_llm_manager)


def test_app_starts_to_login_page(tmp_path, monkeypatch):
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(auth_manager, "DB_PATH", tmp_path / "users.db")
    app = AppTest.from_file(str(Path(__file__).resolve().parent.parent / "streamlit_app.py"), default_timeout=30)
    app.run()
    assert not app.exception
    assert any("Finance Dashboard Pro" in t.value for t in app.title)
