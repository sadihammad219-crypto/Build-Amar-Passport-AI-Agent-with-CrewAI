import json
from crewai import Task


def create_fee_task(agent, applicant_profile, passport_data, policy_task):
    return Task(
        description=f"""
        Calculate the applicant's Bangladesh e-passport fee.

        APPLICANT PROFILE:
        {json.dumps(applicant_profile, indent=2, ensure_ascii=False)}

        LOCAL FEE DATABASE:
        {json.dumps(passport_data.get("fees_2026", {}), indent=2, ensure_ascii=False)}

        FEE DATABASE NOTES:
        {json.dumps(passport_data.get("meta", {}), indent=2, ensure_ascii=False)}

        POLICY DECISION:
        Read and use the Policy Guardian's output provided in your
        task context before selecting a fee.

        REQUIREMENTS:
        1. Check page count: 48 or 64 pages.
        2. Check validity: 5 or 10 years.
        3. Check delivery type: regular, express, or super_express.
        4. Use the exact matching fee from the supplied database.
        5. If the requested validity is ineligible, flag the conflict.
           Do not present its fee as an approved application fee.
        6. If useful, report the fee for an eligible alternative validity
           only when the policy context clearly permits that alternative.
        7. The database says whether VAT is already included. Never add
           VAT twice. Do not calculate or invent an extra charge.
        8. If a required value is missing, invalid, or uncertain, report it.
        9. Identify that the supplied fee schedule needs official
           verification if it has not been verified.

        Do not invent fees or override the Policy Guardian's decision.
        """,

        expected_output="""
        A fee report containing:
        - Page count
        - Eligibility decision used
        - Validity used for the calculation
        - Delivery type
        - Base fee, if available in the database
        - VAT inclusion status
        - Total fee in BDT
        - Any eligibility conflict or verification warning
        """,

        agent=agent,
        context=[policy_task]
    )
