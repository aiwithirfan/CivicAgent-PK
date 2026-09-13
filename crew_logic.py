"""
CivicAgent PK — CrewAI Multi-Agent Workflow

Workflow:

Parser Agent
     ↓
Auditor Agent
     ↓
Drafter Agent
     ↓
Final JSON Response
"""

import json
import os
import re

from crewai import Agent, Crew, Process, Task
from langchain_groq import ChatGroq


# =========================================================
# GROQ API KEY
# =========================================================

def get_groq_api_key():

    try:

        import streamlit as st

        if "GROQ_API_KEY" in st.secrets:

            return str(
                st.secrets["GROQ_API_KEY"]
            )

    except Exception:
        pass

    return os.getenv(
        "GROQ_API_KEY",
        "",
    )


# =========================================================
# MODEL
# =========================================================

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile",
)


# =========================================================
# JSON CLEANER
# =========================================================

def _extract_json(text: str) -> dict:

    if not text:
        return {}

    text = str(text).strip()

    # Remove markdown fences
    text = re.sub(
        r"```json",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = text.replace(
        "```",
        "",
    ).strip()

    # Direct JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # Find JSON object
    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL,
    )

    if match:

        try:

            return json.loads(
                match.group(0)
            )

        except Exception:
            pass

    return {}


# =========================================================
# MAIN CREW
# =========================================================

def run_civic_crew(
    complaint_text: str,
    retrieved_policies: list,
) -> dict:

    api_key = get_groq_api_key()

    # -----------------------------------------------------
    # API KEY CHECK
    # -----------------------------------------------------

    if not api_key:

        return {
            "department": "Municipal Services",
            "priority": "Medium",
            "official_reply_en": (
                "Your complaint has been received "
                "and forwarded to the relevant "
                "department for review."
            ),
            "category": "General",
        }

    # -----------------------------------------------------
    # LLM
    # -----------------------------------------------------

    try:

        llm = ChatGroq(
            model=GROQ_MODEL,
            temperature=0.2,
            groq_api_key=api_key,
        )

    except Exception as e:

        print(
            f"Could not initialize Groq LLM: {e}"
        )

        return {
            "department": "Municipal Services",
            "priority": "Medium",
            "official_reply_en": (
                "Your complaint has been received "
                "and forwarded to the relevant "
                "department for review."
            ),
            "category": "General",
        }

    # =====================================================
    # POLICY CONTEXT
    # =====================================================

    policy_context_parts = []

    for policy in (
        retrieved_policies or []
    ):

        if isinstance(
            policy,
            dict,
        ):

            text = policy.get(
                "text",
                "",
            )

            if text:
                policy_context_parts.append(
                    text
                )

        elif isinstance(
            policy,
            str,
        ):

            policy_context_parts.append(
                policy
            )

    policy_context = (
        "\n\n--- POLICY ---\n\n".join(
            policy_context_parts
        )
        if policy_context_parts
        else
        "No specific policy was retrieved."
    )

    # =====================================================
    # AGENT 1 — PARSER
    # =====================================================

    parser_agent = Agent(
        role="Complaint Parser",
        goal=(
            "Analyze and structure citizen complaints "
            "accurately."
        ),
        backstory=(
            "You are a municipal complaint intake "
            "specialist. You identify the main issue, "
            "category, department and urgency without "
            "inventing facts."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm,
    )

    parser_task = Task(
        description=f"""
Analyze this citizen complaint:

{complaint_text}

Identify:

1. Main issue
2. Complaint category
3. Relevant municipal department
4. Priority: High, Medium, or Low
5. Important facts explicitly stated by the citizen

Return ONLY valid JSON:

{{
    "issue": "...",
    "category": "...",
    "department": "...",
    "priority": "...",
    "facts": ["...", "..."]
}}
""",
        expected_output=(
            "A valid JSON object containing "
            "issue, category, department, "
            "priority and facts."
        ),
        agent=parser_agent,
    )

    # =====================================================
    # AGENT 2 — AUDITOR
    # =====================================================

    auditor_agent = Agent(
        role="Municipal Policy Auditor",
        goal=(
            "Check the parsed complaint against "
            "retrieved civic policies."
        ),
        backstory=(
            "You are a careful municipal policy auditor. "
            "You compare citizen complaints with available "
            "policy information and clearly distinguish "
            "supported information from missing information."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm,
    )

    auditor_task = Task(
        description=f"""
Review the complaint and available policy context.

COMPLAINT:
{complaint_text}

AVAILABLE POLICY CONTEXT:
{policy_context}

Your job:

1. Determine which policy information is relevant.
2. Identify whether the complaint is supported by "
   available policy context.
3. Identify any missing information.
4. Confirm or correct the department.
5. Confirm or correct the priority.
6. Do not invent laws, rules, penalties or government "
   procedures that are not present in the provided context.

Return ONLY valid JSON:

{{
    "policy_relevance": "...",
    "policy_basis": "...",
    "department": "...",
    "priority": "...",
    "audit_notes": "..."
}}
""",
        expected_output=(
            "A valid JSON object containing "
            "policy relevance, policy basis, "
            "department, priority and audit notes."
        ),
        agent=auditor_agent,
        context=[parser_task],
    )

    # =====================================================
    # AGENT 3 — DRAFTER
    # =====================================================

    drafter_agent = Agent(
        role="Official Response Drafter",
        goal=(
            "Draft a professional, concise and "
            "citizen-friendly official response."
        ),
        backstory=(
            "You are an experienced municipal "
            "communications officer. You write clear "
            "official replies based only on the complaint "
            "and verified policy context."
        ),
        verbose=False,
        allow_delegation=False,
        llm=llm,
    )

    drafter_task = Task(
        description=f"""
Prepare the final official response.

Citizen complaint:
{complaint_text}

Available policy:
{policy_context}

Use the Parser and Auditor outputs.

Requirements:

1. Select the correct department.
2. Use High, Medium or Low priority.
3. Give a concise professional official reply.
4. Do not make unsupported legal claims.
5. Do not invent case numbers or deadlines.
6. Clearly acknowledge the citizen's complaint.
7. The response must be suitable for a Pakistani "
   municipal authority.
8. Output ONLY valid JSON.

Required format:

{{
    "department": "...",
    "priority": "High/Medium/Low",
    "category": "...",
    "official_reply_en": "..."
}}
""",
        expected_output=(
            "A valid JSON object with department, "
            "priority, category and official_reply_en."
        ),
        agent=drafter_agent,
        context=[
            parser_task,
            auditor_task,
        ],
    )

    # =====================================================
    # CREW
    # =====================================================

    crew = Crew(
        agents=[
            parser_agent,
            auditor_agent,
            drafter_agent,
        ],
        tasks=[
            parser_task,
            auditor_task,
            drafter_task,
        ],
        process=Process.sequential,
        verbose=False,
    )

    # =====================================================
    # EXECUTE
    # =====================================================

    try:

        result = crew.kickoff()

        result_text = str(result)

        analysis = _extract_json(
            result_text
        )

        if not analysis:

            raise ValueError(
                "CrewAI did not return valid JSON."
            )

        # -------------------------------------------------
        # Normalize output
        # -------------------------------------------------

        return {
            "department": analysis.get(
                "department",
                "Municipal Services",
            ),

            "priority": analysis.get(
                "priority",
                "Medium",
            ),

            "category": analysis.get(
                "category",
                "General",
            ),

            "official_reply_en": analysis.get(
                "official_reply_en",
                (
                    "Your complaint has been received "
                    "and forwarded to the relevant "
                    "department for review."
                ),
            ),
        }

    except Exception as e:

        print(
            f"CrewAI Error: {e}"
        )

        return {
            "department": "Municipal Services",
            "priority": "Medium",
            "category": "General",
            "official_reply_en": (
                "Your complaint has been received "
                "and forwarded to the relevant "
                "department for review."
            ),
        }
