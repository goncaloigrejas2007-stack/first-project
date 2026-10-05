import json
import logging
import os
import urllib.error
import urllib.request

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "llama-3.1-8b-instant"
REQUEST_TIMEOUT = 30
MAX_QUESTION_LENGTH = 1000

logger = logging.getLogger(__name__)


class LLMManager:
    """Minimal Groq chat client (stdlib only)."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model = model

    def get_financial_advice(self, finance_data: dict, question: str = "") -> str:
        question = (question or "").strip()[:MAX_QUESTION_LENGTH]
        if not question:
            question = "Give me short, practical advice about my finances."
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a concise personal finance assistant. Only use the "
                        "summary data provided. Amounts are in euros."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Financial summary: {json.dumps(finance_data, default=str)}\n\nQuestion: {question}",
                },
            ],
            "temperature": 0.3,
            "max_tokens": 500,
        }
        request = urllib.request.Request(
            GROQ_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": "Bearer " + self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                body = json.loads(response.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
        except Exception:
            logger.exception("Groq request failed")
            return "The AI assistant is currently unavailable. Please try again later."


def get_llm_manager():
    """Return an LLMManager if GROQ_API_KEY is configured, otherwise None."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not api_key or api_key == "your_groq_api_key_here":
        return None
    return LLMManager(api_key, os.getenv("GROQ_MODEL", DEFAULT_MODEL))
