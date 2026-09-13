"""
CivicAgent PK — Groq Whisper Voice-to-Text
Supports English, Urdu, Roman Urdu and Urdu + English.
"""

import os
import re
from typing import Any, Dict

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    Groq,
    RateLimitError,
)


# =========================================================
# API KEY
# =========================================================

def get_groq_api_key() -> str:

    # Streamlit Cloud Secrets
    try:

        import streamlit as st

        if "GROQ_API_KEY" in st.secrets:

            return str(
                st.secrets["GROQ_API_KEY"]
            )

    except Exception:
        pass

    # Local environment
    return os.getenv(
        "GROQ_API_KEY",
        "",
    )


# =========================================================
# WHISPER MODEL
# =========================================================

WHISPER_MODEL = os.getenv(
    "GROQ_WHISPER_MODEL",
    "whisper-large-v3-turbo",
)


# =========================================================
# LANGUAGE DETECTION
# =========================================================

def _urdu_character_count(
    text: str,
) -> int:

    if not text:
        return 0

    return len(
        re.findall(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]",
            text,
        )
    )


def _latin_character_count(
    text: str,
) -> int:

    if not text:
        return 0

    return len(
        re.findall(
            r"[A-Za-z]",
            text,
        )
    )


# =========================================================
# ENGLISH
# =========================================================

ENGLISH_WORDS = {
    "a", "about", "after", "again", "all", "am", "an",
    "and", "are", "as", "at", "be", "been", "before",
    "but", "by", "can", "could", "did", "do", "does",
    "for", "from", "get", "go", "good", "have", "he",
    "hello", "help", "her", "here", "how", "i", "if",
    "in", "is", "it", "its", "just", "know", "like",
    "me", "my", "need", "no", "not", "of", "on", "or",
    "our", "please", "problem", "report", "she", "so",
    "some", "that", "the", "their", "there", "they",
    "this", "to", "was", "we", "were", "what", "when",
    "where", "which", "who", "why", "will", "with",
    "would", "yes", "you", "your",
}


def _english_score(
    text: str,
) -> int:

    words = re.findall(
        r"[A-Za-z]+",
        text.lower(),
    )

    return sum(
        1
        for word in words
        if word in ENGLISH_WORDS
    )


def _looks_like_english(
    text: str,
) -> bool:

    words = re.findall(
        r"[A-Za-z]+",
        text.lower(),
    )

    if not words:
        return False

    score = _english_score(text)

    if len(words) <= 8 and score >= 2:
        return True

    if len(words) >= 5:

        ratio = (
            score / len(words)
        )

        if ratio >= 0.45:
            return True

    return False


# =========================================================
# ROMAN URDU
# =========================================================

ROMAN_URDU_WORDS = {
    "mein", "main", "mujhe", "mujhay",
    "mera", "meri", "mere",
    "hum", "ham", "aap", "ap",
    "apka", "apki", "apke",
    "hai", "hain", "tha", "thi", "the",
    "ho", "hun", "houn",
    "kar", "karo", "karen",
    "karta", "karti", "karte",
    "raha", "rahi", "rahe",
    "nahi", "nahin", "nai",
    "ka", "ki", "ke", "ko",
    "se", "par", "pe",
    "yeh", "yah", "woh", "wo",
    "kya", "kyun", "kyon",
    "kab", "kahan", "kidhar", "kaise",
    "aisa", "aisi", "aisay",
    "bohat", "bahut",
    "acha", "achha",
    "achi", "achhi",
    "pani", "paani",
    "bijli",
    "masla",
    "shikayat",
    "gali",
    "sadak",
    "mohalla",
    "ghar",
    "school",
    "hospital",
    "awam",
    "log",
    "hamara",
    "hamari",
    "hamare",
    "madad",
    "chahiye",
    "chahta",
    "chahti",
    "kripya",
    "please",
}


def _roman_urdu_score(
    text: str,
) -> int:

    words = re.findall(
        r"[A-Za-z]+",
        text.lower(),
    )

    return sum(
        1
        for word in words
        if word in ROMAN_URDU_WORDS
    )


def _looks_like_roman_urdu(
    text: str,
) -> bool:

    words = re.findall(
        r"[A-Za-z]+",
        text.lower(),
    )

    if not words:
        return False

    score = _roman_urdu_score(text)

    if len(words) <= 8 and score >= 2:
        return True

    if len(words) >= 5:

        ratio = (
            score / len(words)
        )

        if ratio >= 0.30:
            return True

    return False


# =========================================================
# FINAL LANGUAGE CLASSIFICATION
# =========================================================

def _classify_transcription_language(
    text: str,
    whisper_language_code: str | None,
) -> str:

    if not text:
        return "Unknown"

    text = " ".join(
        text.split()
    )

    urdu_count = (
        _urdu_character_count(text)
    )

    latin_count = (
        _latin_character_count(text)
    )

    has_urdu_script = urdu_count > 0
    has_latin = latin_count > 0

    # Urdu + English
    if has_urdu_script and has_latin:

        if (
            urdu_count >= 3
            and latin_count >= 3
        ):
            return "Urdu + English"

        return "Urdu"

    # Urdu
    if has_urdu_script:
        return "Urdu"

    # Latin script
    if has_latin:

        roman_urdu = (
            _looks_like_roman_urdu(text)
        )

        english = (
            _looks_like_english(text)
        )

        if roman_urdu and english:

            if whisper_language_code:

                code = (
                    whisper_language_code.lower()
                )

                if code.startswith("en"):
                    return "English"

            return "Roman Urdu"

        if roman_urdu:
            return "Roman Urdu"

        if english:
            return "English"

    # Whisper fallback
    if whisper_language_code:

        code = (
            whisper_language_code.lower()
        )

        if code.startswith("ur"):
            return "Urdu"

        if code.startswith("en"):
            return "English"

    return "Unsupported"


# =========================================================
# ERROR HANDLING
# =========================================================

def _handle_groq_error(
    exc: Exception,
) -> str:

    if isinstance(
        exc,
        AuthenticationError,
    ):

        return (
            "Groq authentication failed. "
            "Please check GROQ_API_KEY."
        )

    if isinstance(
        exc,
        RateLimitError,
    ):

        return (
            "Groq API rate limit reached. "
            "Please try again later."
        )

    if isinstance(
        exc,
        APITimeoutError,
    ):

        return (
            "Groq transcription request timed out."
        )

    if isinstance(
        exc,
        APIConnectionError,
    ):

        return (
            "Could not connect to Groq. "
            "Please check your internet connection."
        )

    if isinstance(
        exc,
        BadRequestError,
    ):

        return (
            "Groq could not process this audio. "
            "Please record the complaint again."
        )

    if isinstance(
        exc,
        APIStatusError,
    ):

        status = getattr(
            exc,
            "status_code",
            0,
        )

        return (
            f"Groq API returned an error "
            f"(status {status})."
        )

    return (
        f"Transcription error: {str(exc)}"
    )


# =========================================================
# MAIN TRANSCRIPTION
# =========================================================

def transcribe_audio(
    uploaded_file,
) -> Dict[str, Any]:

    filename = getattr(
        uploaded_file,
        "name",
        "recording.wav",
    )

    result = {
        "success": False,
        "text": None,
        "language": None,
        "language_code": None,
        "source": "voice",
        "filename": filename,
        "error": None,
    }

    # -----------------------------------------------------
    # API KEY
    # -----------------------------------------------------

    api_key = get_groq_api_key()

    if not api_key:

        result["error"] = (
            "Groq API key is not configured. "
            "Please add GROQ_API_KEY to Streamlit Secrets."
        )

        return result

    # -----------------------------------------------------
    # AUDIO BYTES
    # -----------------------------------------------------

    try:

        file_bytes = (
            uploaded_file.getvalue()
        )

    except Exception as exc:

        result["error"] = (
            f"Could not read audio file: {str(exc)}"
        )

        return result

    if not file_bytes:

        result["error"] = (
            "Audio file is empty."
        )

        return result

    # -----------------------------------------------------
    # GROQ
    # -----------------------------------------------------

    try:

        client = Groq(
            api_key=api_key
        )

        transcription = (
            client.audio.transcriptions.create(
                file=(
                    filename,
                    file_bytes,
                ),
                model=WHISPER_MODEL,
                response_format="verbose_json",
                temperature=0.0,
            )
        )

        # -------------------------------------------------
        # TEXT
        # -------------------------------------------------

        text = getattr(
            transcription,
            "text",
            "",
        ) or ""

        text = " ".join(
            text.split()
        )

        if not text:

            result["error"] = (
                "No speech could be detected. "
                "Please record your complaint again."
            )

            return result

        # -------------------------------------------------
        # LANGUAGE
        # -------------------------------------------------

        language_code = getattr(
            transcription,
            "language",
            None,
        )

        final_language = (
            _classify_transcription_language(
                text=text,
                whisper_language_code=language_code,
            )
        )

        # -------------------------------------------------
        # UNSUPPORTED
        # -------------------------------------------------

        if final_language == "Unsupported":

            result["text"] = text

            result["language_code"] = (
                language_code
            )

            result["error"] = (
                "Unsupported language detected. "
                "CivicAgent PK supports English, Urdu, "
                "Roman Urdu, and Urdu + English."
            )

            return result

        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        result.update(
            {
                "success": True,
                "text": text,
                "language": final_language,
                "language_code": language_code,
            }
        )

        return result

    except (
        AuthenticationError,
        RateLimitError,
        APITimeoutError,
        APIConnectionError,
        BadRequestError,
        APIStatusError,
    ) as exc:

        result["error"] = (
            _handle_groq_error(exc)
        )

        return result

    except Exception as exc:

        result["error"] = (
            f"Unexpected transcription error: "
            f"{str(exc)}"
        )

        return result
