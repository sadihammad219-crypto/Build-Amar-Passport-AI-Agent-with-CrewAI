import os
from dotenv import load_dotenv
from crewai import LLM

load_dotenv()


def create_llm():
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("MODEL", "gemini/gemini-3.8-flash")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from .env")

    return LLM(
        model=model,
        api_key=api_key,
        temperature=0.2
    )
