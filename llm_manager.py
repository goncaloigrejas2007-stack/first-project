import os

from dotenv import load_dotenv
from groq import Groq


MODEL = "llama-3.3-70b-versatile"


class LLMManager:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def get_financial_advice(self, finance_data):
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a personal finance assistant. Give clear, practical "
                    "general guidance based only on the financial data provided. "
                    "Do not present yourself as a financial professional."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Review these personal finance figures and give a brief helpful "
                    f"summary:\n{finance_data}"
                ),
            },
        ]
        try:
            response = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.5,
                max_tokens=500,
            )
            return response.choices[0].message.content or "No advice was returned."
        except Exception:
            return "The AI assistant is temporarily unavailable. Please try again later."


def get_llm_manager():
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    return LLMManager(api_key) if api_key else None
