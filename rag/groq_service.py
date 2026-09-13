import json
import os

from dotenv import load_dotenv
from groq import Groq

from .prompts import SYSTEM_PROMPT

load_dotenv()


def get_client() -> Groq:
    """
    Create and return the Groq client.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key or api_key == "your_groq_api_key_here":
        raise RuntimeError(
            "GROQ_API_KEY is missing. "
            "Create a .env file and add your Groq API key."
        )

    return Groq(api_key=api_key)


def generate_response(
    user_prompt: str,
    system_prompt: str = SYSTEM_PROMPT,
) -> str:
    """
    Send a prompt to Groq and return the model response.
    """

    if not user_prompt.strip():
        raise ValueError("User prompt cannot be empty.")

    model = os.getenv(
        "GROQ_MODEL",
        "llama-3.3-70b-versatile",
    )

    client = get_client()

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        temperature=0.1,
    )

    return completion.choices[0].message.content.strip()


def generate_structured_response(
    user_prompt: str,
) -> dict:
    """
    Generate a JSON response from Groq and parse it into a dictionary.
    """

    response = generate_response(user_prompt)

    try:
        return json.loads(response)

    except json.JSONDecodeError:
        # Handle accidental Markdown code fences.
        cleaned = response.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]

        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError as error:
            raise ValueError(
                "Groq returned invalid JSON.\n\n"
                f"Raw response:\n{response}"
            ) from error