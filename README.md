# Finance Flow

A small SaaS-style personal finance web app with:
- user registration and login
- private area per user
- income and expense tracking
- AI assistant for financial tips and planning
- built in Python with FastAPI

## Features
- Registration and login with hashed passwords
- JWT cookie-based authentication
- Dashboard with totals and recent transactions
- Add income or expense records
- Chat with an LLM-style assistant
- Works with SQLite by default
- Optional OpenAI API integration

## Tech stack
- FastAPI
- SQLAlchemy
- SQLite
- Jinja2 templates
- HTML/CSS/JavaScript
- Optional OpenAI API

## Local setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy environment file:
   ```bash
   cp .env.example .env
   ```

4. Set your secret key and, optionally, your OpenAI API key:
   ```bash
   SECRET_KEY=your-secret-key
   OPENAI_API_KEY=your-api-key-if-needed
   ```

5. Run the app:
   ```bash
   uvicorn app:app --reload
   ```

6. Open the app in your browser:
   ```text
   http://127.0.0.1:8000
   ```

## Default flow
- Register a user account
- Log in
- Add your income and expenses in the dashboard
- Use the AI assistant to ask for insights, budget suggestions, or summaries

## Notes
- SQLite is used for easy local development.
- If `OPENAI_API_KEY` is not configured, the assistant will still provide a helpful local financial response.
- For production, move to PostgreSQL and a stronger deployment setup.
