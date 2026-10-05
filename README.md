# 💰 Finance Dashboard Pro

A personal finance dashboard built with Python and Streamlit. Create an account, track income and expenses, set monthly budgets and savings goals, and explore your spending with charts. Everything runs locally and is stored in SQLite.

![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-app-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

## Screenshots

Screenshots can be added to [`docs/screenshots/`](docs/screenshots/).

---

## ✨ Features

### 👤 Accounts
- Register and log in with a username, email and password
- Each user only sees their own transactions, budgets and goals
- Passwords are hashed with bcrypt
- Per-user settings: light/dark theme and a notifications checkbox (the preference is saved, but no notifications are sent yet)

### 📝 Transactions
- Add income and expenses with amount, category, description and date
- Add transactions from the **Transactions** tab, or from an expander in the **Overview** tab
- Create your own categories, each with an emoji
- Filter by category and date range, and sort by date or amount
- Edit or delete any transaction
- Export the filtered list as CSV

### 📊 Overview and analytics
- Headline metrics: total spending, total income, net balance, average transaction, and a 30-day spending forecast (shown once you have expenses on at least 7 different days)
- Smart insights: top spending category, unusually large transactions, and the 30-day average
- This month's spending and income
- Charts (Altair): monthly spending trend, spending by category (bar), category distribution (pie)
- Statistics: median, standard deviation, highest and lowest expense

### 🎯 Budget
- A monthly budget for every category
- Budget vs. actual spending for the current month, with a progress bar per category
- 🟢 under 75% used, 🟡 above 75%, 🔴 over budget
- Save your changes or reset to the defaults

### 💼 Savings goals
- Create goals with a target amount and an optional description
- Add contributions and track progress with progress bars
- Delete goals you no longer need

### 🎨 Theme
- Light and dark themes, applied immediately from the sidebar
- Click **Save settings** to keep your choice for the next login

---

## 🚀 Quick start

### Requirements
- Python 3.9 or higher

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/goncaloigrejas2007-stack/first-project.git
cd first-project
```

2. **Create a virtual environment** (recommended)
```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

3. **Install the dependencies**
```bash
pip install -r requirements.txt
```

4. **Run the app**
```bash
streamlit run streamlit_app.py
```

5. **Open it in your browser** at `http://localhost:8501`

> If `pip` or `streamlit` is not on your PATH, use `python -m pip` and `python -m streamlit` instead.

The databases are created automatically on first run. To use the app again later, activate the virtual environment first (`source .venv/bin/activate`), then run the last command.

---

## 📖 How to use

1. **Register** a new account, then **log in**. Passwords need at least 8 characters, with a letter and a digit.
2. Open the **Transactions** tab and fill in the **Add transaction** form at the top. You can also use the **Add transaction** expander in the **Overview** tab.
3. To add a category of your own, use **Manage categories** in the **Transactions** tab.
4. Open **Budget** to set monthly limits per category and see how you are doing this month.
5. Open **Savings** to create goals and add contributions.
6. Open **Analytics** for charts and statistics.
7. In **Transactions**, filter and sort your history, edit or delete entries, or export a CSV.

---

## 📁 Project structure

```
first-project/
├── streamlit_app.py          # Streamlit user interface
├── auth_manager.py           # Registration, login and user settings
├── db.py                     # Finance database schema and CRUD operations
├── analytics.py              # Budget summaries, forecasts and exports
├── theme.py                  # Theme palettes and chart styling
├── requirements.txt          # Python dependencies
├── requirements-dev.txt      # Development and test dependencies
├── test_*.py                 # Authentication, analytics and UI tests
├── .github/workflows/ci.yml  # Tests on pushes and pull requests
├── docs/screenshots/         # Project screenshots
├── .streamlit/config.toml    # Streamlit defaults (accent color and font)
├── .gitignore                # Local files and databases to ignore
├── LICENSE                   # MIT license
└── README.md                 # This file
```

---

## 🛠️ Tech stack

| Technology | Purpose |
|-----------|---------|
| **Python** | Programming language |
| **Streamlit** | Web interface |
| **Pandas** | Data processing |
| **Altair** | Charts |
| **SQLite** | Local databases |
| **bcrypt** | Password hashing |

---

## 📝 Default categories and budgets

| Category | Monthly budget |
|----------|---------------:|
| 🍔 Food & Dining | €500 |
| 🚗 Transport | €150 |
| 🎬 Entertainment | €300 |
| 💡 Utilities | €200 |
| 🏃 Health & Fitness | €150 |
| 🛍️ Shopping | €250 |
| 📚 Education | €200 |
| 📺 Subscriptions | €100 |
| ✈️ Travel & Holidays | €400 |
| 💅 Personal Care | €100 |
| 📦 Other | €200 |

**Income** is a special category for earnings. It has no budget and is not counted as spending. A custom category gets a default budget of €100.

You can change any budget in the **Budget** tab.

---

## 💾 Data storage

The app uses two SQLite files, created next to the code:

| File | Contents |
|------|----------|
| `users.db` | Accounts (username, email, password hash) and settings |
| `finance_data.db` | Transactions, budgets, savings goals and custom categories |

Both files are ignored by git. To store them somewhere else, set these environment variables before starting the app:

```bash
export AUTH_DB_PATH=/path/to/users.db
export FINANCE_DB_PATH=/path/to/finance_data.db
```

**Back up your data** by copying both files:
```bash
cp users.db users.db.backup
cp finance_data.db finance_data.db.backup
```

---

## 🔐 Privacy and security

- All data stays on the machine that runs the app. Nothing is sent to any external service.
- Passwords are stored as bcrypt hashes, never as plain text.
- Database queries are parameterized, and finance records are scoped to each user.
- `.db` files and `.env` files are ignored by git.
- Login errors are generic, so they do not reveal whether a username exists.
- This is a personal project for local use. It has no rate limiting, no password reset and no session persistence (refreshing the page logs you out). It is not designed to be exposed on the public internet.

---

## 🧪 Testing

Install development dependencies and run all tests with:

```bash
pip install -r requirements-dev.txt
pytest
```

The tests cover authentication, analytics, and a Streamlit smoke test. Database tests use temporary SQLite files.

---

## Development notes

This project was developed with the assistance of AI tools, and the code was reviewed by the author.

---

## Nota em português

Projeto desenvolvido com apoio de ferramentas de IA e revisto pelo autor.

---

## 🎯 Ideas for the future

- Recurring transactions
- Importing transactions from CSV
- Real notifications for budget alerts
- More reports

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

Created by **Gonçalo Igrejas** · [@goncaloigrejas2007-stack](https://github.com/goncaloigrejas2007-stack)
