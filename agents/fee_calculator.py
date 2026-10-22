from crewai import Agent
from config.llm import create_llm


def create_fee_calculator():
    return Agent(
        role="Bangladesh Passport Fee Auditor",
        goal=(
            "Calculate the passport application fee in BDT using "
            "the supplied local fee database and the Policy Guardian's "
            "eligibility decision."
        ),
        backstory=(
            "You are a meticulous financial auditor specializing in "
            "Bangladesh e-passport fees. Check page count, permitted "
            "validity, and delivery speed before selecting a fee. "
            "Use the supplied database exactly. If its metadata says "
            "VAT is included, never add VAT twice. Never invent fees. "
            "Flag invalid validity requests and fees requiring official "
            "verification."
        ),
        llm=create_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )
