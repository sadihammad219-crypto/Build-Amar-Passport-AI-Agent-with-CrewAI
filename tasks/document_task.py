import json
from crewai import Task


def create_document_task(
    agent,
    applicant_profile,
    passport_data,
    policy_task,
    fee_task
):
    return Task(
        description=f"""
        Prepare a personalized Bangladesh e-passport document checklist.

        APPLICANT PROFILE:
        {json.dumps(applicant_profile, indent=2, ensure_ascii=False)}

        LOCAL DOCUMENT DATABASE:
        {json.dumps(passport_data.get("required_docs", {}), indent=2, ensure_ascii=False)}

        POLICY REFERENCE:
        Use the Policy Guardian's output in your context to understand
        the applicant's age group, eligibility, and identification needs.

        FEE REFERENCE:
        Use the Fee Calculator's output in your context when relevant.

        REQUIREMENTS:
        1. Create a checklist appropriate to the applicant's age.
        2. Consider the applicant's profession, including government
           employment and any applicable GO/NOC requirements.
        3. Consider name changes and supporting legal documents,
           including a Marriage Certificate where applicable.
        4. Include parents' NID for minors where applicable.
        5. Include the application summary and payment slip where
           indicated by the supplied local database.
        6. Separate likely required documents from conditional documents.
        7. Do not claim that a document is mandatory unless supported
           by the supplied data or verified official guidance.
        8. Clearly flag any requirement that needs official verification.

        Do not calculate fees or change the Policy Guardian's decision.
        """,

        expected_output="""
        A customized document checklist containing:
        - Applicant category
        - Documents to prepare
        - Conditional documents and when they apply
        - Missing information
        - Official verification warnings
        """,

        agent=agent,
        context=[policy_task, fee_task]
    )
