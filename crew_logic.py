import os
import json
from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq

def run_civic_crew(complaint_text: str, retrieved_policies: list) -> dict:
    """
    Irfan Shah's Multi-Agent Logic for CivicAgent PK.
    Uses CrewAI and Groq API to analyze complaints and draft resolutions.
    """
    
    # 1. Initialize Groq LLM (Make sure GROQ_API_KEY is in your environment variables/secrets)
    llm = ChatGroq(
        temperature=0.3,
        model_name="llama3-8b-8192", 
        api_key=os.environ.get("GROQ_API_KEY")
    )

    # 2. Define the AI Agent
    municipal_officer = Agent(
        role='Senior Municipal Officer',
        goal='Analyze citizen complaints against government policies and draft an official resolution.',
        backstory=(
            "You are a highly experienced government official in Pakistan. "
            "You receive citizen complaints, review them against standard operating procedures, "
            "and draft professional, empathetic, and actionable official replies."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm
    )

    # 3. Define the Task
    policy_context = "\n".join([p.get('text', '') for p in retrieved_policies]) if retrieved_policies else "No specific policy found."
    
    analysis_task = Task(
        description=(
            f"Analyze the following citizen complaint:\n'{complaint_text}'\n\n"
            f"Based on these official policies:\n'{policy_context}'\n\n"
            "Task Requirements:\n"
            "1. Identify the relevant government department.\n"
            "2. Assign a priority (High, Medium, Low).\n"
            "3. Draft a short official reply in English addressing the citizen.\n"
            "4. Categorize the issue (e.g., Sanitation, Electricity, Roads).\n\n"
            "Output strictly as a valid JSON dictionary with keys: 'department', 'priority', 'official_reply_en', 'category'."
        ),
        expected_output='JSON dictionary with keys: department, priority, official_reply_en, category.',
        agent=municipal_officer
    )

    # 4. Form the Crew and Execute
    crew = Crew(
        agents=[municipal_officer],
        tasks=[analysis_task],
        process=Process.sequential
    )

    # 5. Kickoff and parse result
    try:
        result_text = crew.kickoff()
        # Clean up the output to ensure it's a valid dictionary
        result_str = str(result_text).replace('```json', '').replace('```', '').strip()
        analysis_result = json.loads(result_str)
        return analysis_result
    except Exception as e:
        print(f"CrewAI Error: {e}")
        # Fallback response if parsing fails
        return {
            "department": "Municipal Services",
            "priority": "Medium",
            "official_reply_en": "Your complaint has been received and forwarded to the relevant department for review.",
            "category": "General Inquiry"
        }