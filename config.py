import os

import streamlit as st
from dotenv import load_dotenv


# ---------------------------------------------------------
# Load local .env file
# ---------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------
# Groq API key
# ---------------------------------------------------------

def _get_groq_api_key() -> str:
    """
    Get Groq API key safely.

    Priority:
    1. Streamlit Secrets - deployment
    2. Environment variable - local development
    """

    # Streamlit Cloud
    try:
        secret_key = st.secrets.get("GROQ_API_KEY")

        if secret_key:
            return str(secret_key).strip()

    except Exception:
        pass

    # Local development
    env_key = os.getenv("GROQ_API_KEY")

    if env_key:
        return env_key.strip()

    return ""


GROQ_API_KEY = _get_groq_api_key()


# ---------------------------------------------------------
# Whisper model
# ---------------------------------------------------------

MODEL_NAME = "whisper-large-v3"


# ---------------------------------------------------------
# Audio file limits
# ---------------------------------------------------------

MAX_FILE_SIZE_MB = 25


SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".webm",
}


SUPPORTED_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/m4a",
    "audio/webm",
}