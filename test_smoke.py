import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parent / "streamlit_app.py"


class FinanceAppSmokeTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.old_auth_db = os.environ.get("AUTH_DB_PATH")
        self.old_finance_db = os.environ.get("FINANCE_DB_PATH")
        os.environ["AUTH_DB_PATH"] = str(Path(self.temp_dir.name) / "users.db")
        os.environ["FINANCE_DB_PATH"] = str(Path(self.temp_dir.name) / "finance.db")

    def tearDown(self):
        if self.old_auth_db is None:
            os.environ.pop("AUTH_DB_PATH", None)
        else:
            os.environ["AUTH_DB_PATH"] = self.old_auth_db
        if self.old_finance_db is None:
            os.environ.pop("FINANCE_DB_PATH", None)
        else:
            os.environ["FINANCE_DB_PATH"] = self.old_finance_db
        self.temp_dir.cleanup()

    def test_register_login_and_add_transaction(self):
        app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
        self.assertEqual(app.exception, [])

        app.text_input(key="register_username").set_value("smoke-user")
        app.text_input(key="register_email").set_value("smoke@example.com")
        app.text_input(key="register_password").set_value("password123")
        app.text_input(key="register_confirm_password").set_value("password123")
        app.button(key="register_submit").click().run()
        self.assertEqual(app.exception, [])

        app.text_input(key="login_username").set_value("smoke-user")
        app.text_input(key="login_password").set_value("password123")
        app.button(key="login_submit").click().run()
        self.assertEqual(app.exception, [])
        self.assertIn("🎯 Monthly budget", [item.value for item in app.subheader])

        app.number_input(key="tx_amount").set_value(0.0)
        app.button(key="tx_submit").click().run()
        self.assertEqual(app.exception, [])
        self.assertIn("Amount must be greater than 0", [item.value for item in app.warning])

        app.number_input(key="tx_amount").set_value(23.45)
        app.text_input(key="tx_description").set_value("Smoke test transaction")
        app.button(key="tx_submit").click().run()
        self.assertEqual(app.exception, [])

        finance_db = Path(os.environ["FINANCE_DB_PATH"])
        with sqlite3.connect(finance_db) as connection:
            transaction = connection.execute(
                "SELECT amount, description FROM transactions"
            ).fetchone()
        self.assertEqual(transaction, (23.45, "Smoke test transaction"))


if __name__ == "__main__":
    unittest.main()
