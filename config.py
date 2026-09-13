import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _get_secret(name, default=""):
    """Get value from Streamlit Secrets first, then environment."""
    
    try:
        value = st.secrets.get(name)
        if value:
            return str(value).strip()
    except Exception:
        pass

    return os.getenv(name, default).strip()


# ---------------------------------------------------------
# Groq
# ---------------------------------------------------------

GROQ_API_KEY = _get_secret("GROQ_API_KEY")

GROQ_MODEL = _get_secret(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)

GROQ_WHISPER_MODEL = _get_secret(
    "GROQ_WHISPER_MODEL",
    "whisper-large-v3-turbo"
)

# Backward compatibility
MODEL_NAME = GROQ_WHISPER_MODEL


# ---------------------------------------------------------
# Audio
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
