import json
from crewai import Task


def create_policy_task(agent, applicant_profile, policy_data):
    return Task(
        description=f"""
        Evaluate the passport eligibility of this applicant.

        APPLICANT PROFILE:
        {json.dumps(applicant_profile, indent=2, ensure_ascii=False)}

        LOCAL POLICY DATA:
        {json.dumps(policy_data.get("policy_2026", {}), indent=2, ensure_ascii=False)}

        YOUR RESPONSIBILITIES:
        1. Determine the applicant's age group.
        2. Identify permitted passport validity options.
        3. Check the requested validity, if provided.
        4. Flag any age-validity inconsistency.
        5. Identify the applicable NID or Birth Registration requirement.
        6. Mention any uncertainty or policy information requiring
           official verification.
        7. Do not calculate passport fees or invent rules.

        Use the supplied local policy data as your reference.
        Do not silently approve an ineligible request.
        """,

        expected_output="""
        A clear eligibility report containing:
        - Applicant age and age group
        - Requested validity
        - Eligibility status
        - Permitted validity
        - Identification requirements
        - Warnings or inconsistencies
        - Items requiring official verification
        """,

        agent=agent
    )
