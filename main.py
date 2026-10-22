import json
from pathlib import Path

from dotenv import load_dotenv
from crewai import Crew, Process, Task

from agents.policy_guardian import create_policy_guardian
from agents.fee_calculator import create_fee_calculator
from agents.document_architect import create_document_architect

from tasks.policy_task import create_policy_task
from tasks.fee_task import create_fee_task
from tasks.document_task import create_document_task


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "config" / "passport_data.json"


def ask_int(prompt, allowed=None, minimum=None, maximum=None):
    while True:
        try:
            value = int(input(prompt).strip())

            if allowed is not None and value not in allowed:
                print("Please choose one of:", ", ".join(map(str, allowed)))
                continue

            if minimum is not None and value < minimum:
                print(f"Value must be at least {minimum}.")
                continue

            if maximum is not None and value > maximum:
                print(f"Value must not exceed {maximum}.")
                continue

            return value

        except ValueError:
            print("Please enter a valid whole number.")


def ask_yes_no(prompt):
    while True:
        answer = input(prompt + " (yes/no): ").strip().lower()

        if answer in ("yes", "y"):
            return True
        if answer in ("no", "n"):
            return False

        print("Please enter yes or no.")


def get_applicant_profile():
    print("\n=== Amar Passport: Applicant Profile ===")

    age = ask_int("Applicant age: ", minimum=0, maximum=120)

    profession = input(
        "Profession (e.g. private sector employee): "
    ).strip()

    if not profession:
        profession = "Not specified"

    page_count = ask_int(
        "Passport pages (48 or 64): ",
        allowed=[48, 64]
    )

    requested_validity = ask_int(
        "Requested validity in years (5 or 10): ",
        allowed=[5, 10]
    )

    while True:
        delivery = input(
            "Delivery type (regular/express/super_express): "
        ).strip().lower().replace(" ", "_").replace("-", "_")

        if delivery in ("regular", "express", "super_express"):
            break

        print("Choose regular, express, or super_express.")

    location = input("City/district (optional): ").strip()

    has_nid = ask_yes_no("Does the applicant have an NID?")
    has_birth_registration = ask_yes_no(
        "Does the applicant have a Birth Registration Certificate?"
    )
    name_change = ask_yes_no(
        "Does the application involve a name change?"
    )

    return {
        "age": age,
        "profession": profession,
        "page_count": page_count,
        "requested_validity_years": requested_validity,
        "delivery_type": delivery,
        "location": location or "Not specified",
        "has_nid": has_nid,
        "has_birth_registration": has_birth_registration,
        "name_change": name_change,
    }


def build_local_fallback(profile, data):
    """Generate a basic report from local JSON if CrewAI fails."""

    age = profile["age"]
    requested_years = profile["requested_validity_years"]
    page_count = profile["page_count"]
    delivery = profile["delivery_type"]
    profession = profile["profession"].lower()

    policy = data.get("policy_2026", {})
    validity_rules = policy.get("validity_by_age", {})

    if age < 18:
        age_group = "Under 18"
        rule = validity_rules.get("under_18", {})
        id_key = "under_18"
        doc_key = "minor_under_18"
    elif age <= 65:
        age_group = "18–65"
        rule = validity_rules.get("age_18_to_65", {})
        id_key = "age_18_to_20" if age <= 20 else "over_20"
        doc_key = "adult"
    else:
        age_group = "Over 65"
        rule = validity_rules.get("over_65", {})
        id_key = "over_20"
        doc_key = "adult"

    allowed_years = rule.get("allowed_years", [])
    eligible = requested_years in allowed_years

    fees = data.get("fees_2026", {})
    page_key = f"{page_count}_pages"
    selected_years = requested_years

    if not eligible:
        if 5 in allowed_years:
            selected_years = 5
        elif allowed_years:
            selected_years = allowed_years[0]

    fee_value = None
    try:
        fee_value = fees[page_key][f"{selected_years}_years"][delivery]
    except (KeyError, TypeError):
        pass

    if eligible:
        if fee_value is None:
            fee_text = "Fee unavailable in local database"
        else:
            fee_text = f"BDT {fee_value:,}"
            if data.get("meta", {}).get("fee_values_include_vat"):
                fee_text += " (VAT included according to local data)"
    else:
        if fee_value is None:
            fee_text = (
                "Not quoted: requested validity is ineligible; "
                "alternative fee unavailable"
            )
        else:
            fee_text = (
                f"Requested validity is NOT ELIGIBLE. "
                f"Conditional {selected_years}-year alternative: "
                f"BDT {fee_value:,}; confirm eligibility officially"
            )

    identification = policy.get(
        "identification_by_age", {}
    ).get(id_key, ["Confirm identification requirements officially"])

    required_docs = data.get("required_docs", {})
    documents = list(required_docs.get(doc_key, []))

    if any(word in profession for word in ("government", "govt", "সরকার")):
        documents.extend(required_docs.get("government_staff", []))

    if any(word in profession for word in ("private", "বেসরকারি")):
        documents.extend(required_docs.get("private_sector", []))

    if profile["name_change"]:
        documents.extend(required_docs.get("name_change", []))

    documents = list(dict.fromkeys(documents))

    if age >= 18 and not profile["has_nid"]:
        documents.append(
            "NID not confirmed: verify the acceptable identification route"
        )

    if age < 18 and not profile["has_birth_registration"]:
        documents.append(
            "Birth Registration not confirmed: check the applicable requirement"
        )

    eligibility_text = (
        "Eligible according to local sample rules"
        if eligible
        else "FLAG: requested validity conflicts with local sample rules"
    )

    rows = [
        ("Applicant age", str(age)),
        ("Age group", age_group),
        ("Profession", profile["profession"]),
        ("Location", profile["location"]),
        ("Eligibility", eligibility_text),
        (
            "Permitted validity in local data",
            ", ".join(f"{year} years" for year in allowed_years) or "Unknown"
        ),
        ("Requested validity", f"{requested_years} years"),
        ("Page count", str(page_count)),
        ("Delivery type", delivery.replace("_", " ").title()),
        ("Fee estimate", fee_text),
        ("Identification guidance", "; ".join(identification)),
        ("Documents checklist", "; ".join(documents)),
        (
            "Fee data status",
            "Assignment sample values; official 2026 schedule not verified"
        ),
    ]

    report = [
        "| Field | Result |",
        "|---|---|",
    ]

    for field, result in rows:
        result = str(result).replace("|", "\\|")
        report.append(f"| {field} | {result} |")

    report.append("")
    report.append(
        "**বাংলা সারাংশ:** এটি local database-ভিত্তিক fallback report। "
        "পাসপোর্টের মেয়াদ, পরিচয়পত্র এবং ফি আবেদনের আগে সরকারি নির্দেশনা "
        "থেকে যাচাই করতে হবে।"
    )

    return "\n".join(report)


def main():
    load_dotenv()

    with DATA_FILE.open("r", encoding="utf-8") as file:
        passport_data = json.load(file)

    profile = get_applicant_profile()

    try:
        # Create the three specialized agents.
        policy_agent = create_policy_guardian()
        fee_agent = create_fee_calculator()
        document_agent = create_document_architect()

        # Policy Guardian evaluates eligibility first.
        policy_task = create_policy_task(
            policy_agent, profile, passport_data
        )

        # Fee Calculator receives the Policy Guardian task as context.
        fee_task = create_fee_task(
            fee_agent, profile, passport_data, policy_task
        )

        # Document Architect receives both earlier tasks as context.
        document_task = create_document_task(
            document_agent,
            profile,
            passport_data,
            policy_task,
            fee_task,
        )

        # The final task formats all findings as an English Markdown table.
        final_report_task = Task(
            description=f"""
            Produce the final Amar Passport Readiness Report.

            APPLICANT PROFILE:
            {json.dumps(profile, indent=2, ensure_ascii=False)}

            Use the outputs of the Policy Guardian, Fee Calculator,
            and Document Architect available in your context.

            OUTPUT REQUIREMENTS:
            1. Start with an English Markdown table with columns Field and Result.
            2. Include age group, eligibility, requested and permitted validity,
               identification guidance, page count, delivery type, total fee,
               documents checklist, and warnings.
            3. Clearly flag a requested validity that is not eligible.
               Never present the fee for an ineligible combination as approved.
            4. Do not add VAT again if the local fee data already includes it.
            5. Do not invent policies, fees, or mandatory documents.
            6. Add a short Bangla summary after the English table.
            7. Clearly state that the local fee sample must be verified
               against the official 2026 fee schedule.
            8. If any information is uncertain, state that explicitly.
            """,
            expected_output=(
                "An English Markdown table containing the complete passport "
                "readiness report, followed by a short Bangla summary and "
                "clear verification warnings."
            ),
            agent=document_agent,
            context=[policy_task, fee_task, document_task],
        )

        crew = Crew(
            agents=[policy_agent, fee_agent, document_agent],
            tasks=[
                policy_task,
                fee_task,
                document_task,
                final_report_task,
            ],
            process=Process.sequential,
            verbose=True,
        )

        print("\nRunning Amar Passport AI Agent...\n")
        result = crew.kickoff()

        print("\n# Amar Passport Readiness Report\n")
        print(result)

    except Exception as exc:
        print(
            "\nCrewAI execution failed "
            f"({type(exc).__name__}). Using local database fallback."
        )

        print("\n# Amar Passport Readiness Report — Local Fallback\n")
        print(build_local_fallback(profile, passport_data))


if __name__ == "__main__":
    main()
