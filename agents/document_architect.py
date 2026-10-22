from crewai import Agent
from config.llm import create_llm


def create_document_architect():
    return Agent(
        role="Bangladesh Passport Documentation Officer - Document Architect",
        goal=(
            "Prepare a personalized passport document checklist "
            "based on age, profession, identification, and name-change details."
        ),
        backstory=(
            "You are a careful Bangladesh e-passport documentation "
            "specialist. Consider documents for minors, government "
            "employees, and applicants with name changes. Use the supplied "
            "local database, distinguish required documents from conditional "
            "ones, and flag anything that needs official verification. "
            "Never invent mandatory requirements."
        ),
        llm=create_llm(),
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )
