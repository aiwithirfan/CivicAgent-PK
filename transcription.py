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

from config import GROQ_API_KEY, MODEL_NAME


# ---------------------------------------------------------
# Urdu script detection
# ---------------------------------------------------------

def _urdu_character_count(text: str) -> int:
    """
    Count Urdu/Arabic-script characters.
    """

    if not text:
        return 0

    return len(
        re.findall(
            r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]",
            text,
        )
    )


def _latin_character_count(text: str) -> int:
    """
    Count Latin alphabet characters.
    """

    if not text:
        return 0

    return len(
        re.findall(
            r"[A-Za-z]",
            text,
        )
    )


# ---------------------------------------------------------
# English detection
# ---------------------------------------------------------

ENGLISH_WORDS = {
    "a", "about", "after", "again", "all", "am", "an", "and",
    "are", "as", "at", "be", "been", "before", "but", "by",
    "can", "could", "did", "do", "does", "for", "from", "get",
    "go", "good", "have", "he", "hello", "help", "her", "here",
    "how", "i", "if", "in", "is", "it", "its", "just", "know",
    "like", "me", "my", "need", "no", "not", "of", "on", "or",
    "our", "please", "problem", "report", "she", "so", "some",
    "that", "the", "their", "there", "they", "this", "to",
    "was", "we", "were", "what", "when", "where", "which",
    "who", "why", "will", "with", "would", "yes", "you", "your",
}


def _english_score(text: str) -> int:
    """
    Count recognizable English words.
    """

    words = re.findall(
        r"[A-Za-z]+",
        text.lower(),
    )

    return sum(
        1
        for word in words
        if word in ENGLISH_WORDS
    )


def _looks_like_english(text: str) -> bool:
    """
    Determine whether text is likely English.
    """

    words = re.findall(
        r"[A-Za-z]+",
        text.lower(),
    )

    if not words:
        return False

    score = _english_score(text)

    # Handles short English phrases such as:
    # "Hello, how are you?"
    if len(words) <= 8 and score >= 2:
        return True

    # Longer English text
    if len(words) >= 5:
        ratio = score / len(words)

        if ratio >= 0.45:
            return True

    return False


# ---------------------------------------------------------
# Roman Urdu detection
# ---------------------------------------------------------

ROMAN_URDU_WORDS = {
    "mein", "main", "mujhe", "mujhay", "mera", "meri", "mere",
    "hum", "ham", "aap", "ap", "apka", "apki", "apke",
    "hai", "hain", "tha", "thi", "the", "ho", "hun", "houn",
    "kar", "karo", "karen", "karta", "karti", "karte",
    "raha", "rahi", "rahe",
    "nahi", "nahin", "nai",
    "ka", "ki", "ke", "ko", "se", "par", "pe",
    "yeh", "yah", "woh", "wo",
    "kya", "kyun", "kyon", "kab", "kahan", "kidhar", "kaise",
    "aisa", "aisi", "aisay",
    "bohat", "bahut",
    "acha", "achha", "achi", "achhi",
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


def _roman_urdu_score(text: str) -> int:
    """
    Count common Roman Urdu words.
    """

    words = re.findall(
        r"[A-Za-z]+",
        text.lower(),
    )

    return sum(
        1
        for word in words
        if word in ROMAN_URDU_WORDS
    )


def _looks_like_roman_urdu(text: str) -> bool:
    """
    Determine whether Latin-script text is likely Roman Urdu.
    """

    words = re.findall(
        r"[A-Za-z]+",
        text.lower(),
    )

    if not words:
        return False

    score = _roman_urdu_score(text)

    # Short Roman Urdu phrases
    if len(words) <= 8 and score >= 2:
        return True

    # Longer Roman Urdu text
    if len(words) >= 5:
        ratio = score / len(words)

        if ratio >= 0.30:
            return True

    return False


# ---------------------------------------------------------
# Language classification
# ---------------------------------------------------------

def _classify_transcription_language(
    text: str,
    whisper_language_code: str | None,
) -> str:
    """
    Classify transcription into:

        English
        Urdu
        Roman Urdu
        Urdu + English

    Any other language is rejected.
    """

    if not text:
        return "Unknown"

    text = " ".join(text.split())

    urdu_count = _urdu_character_count(text)
    latin_count = _latin_character_count(text)

    has_urdu_script = urdu_count > 0
    has_latin = latin_count > 0

    # -----------------------------------------------------
    # Urdu + English
    # -----------------------------------------------------

    if has_urdu_script and has_latin:

        if urdu_count >= 3 and latin_count >= 3:
            return "Urdu + English"

        return "Urdu"

    # -----------------------------------------------------
    # Urdu
    # -----------------------------------------------------

    if has_urdu_script:
        return "Urdu"

    # -----------------------------------------------------
    # Latin-script text
    # -----------------------------------------------------

    if has_latin:

        roman_urdu = _looks_like_roman_urdu(text)
        english = _looks_like_english(text)

        # Both English and Roman Urdu signals
        if roman_urdu and english:

            if whisper_language_code:
                code = whisper_language_code.lower()

                if code.startswith("en"):
                    return "English"

            return "Roman Urdu"

        if roman_urdu:
            return "Roman Urdu"

        if english:
            return "English"

    # -----------------------------------------------------
    # Whisper fallback
    # -----------------------------------------------------

    if whisper_language_code:

        code = whisper_language_code.lower()

        if code.startswith("ur"):
            return "Urdu"

        if code.startswith("en"):
            return "English"

    # -----------------------------------------------------
    # Unsupported
    # -----------------------------------------------------

    return "Unsupported"


# ---------------------------------------------------------
# Groq error handling
# ---------------------------------------------------------

def _handle_groq_error(exc: Exception) -> str:
    """
    Convert Groq/API exceptions into safe user-friendly messages.
    """

    if isinstance(exc, AuthenticationError):
        return (
            "Groq authentication failed. "
            "Please check the configured API key."
        )

    if isinstance(exc, RateLimitError):
        return (
            "Groq API rate limit reached. "
            "Please wait a moment and try again."
        )

    if isinstance(exc, APITimeoutError):
        return (
            "The transcription service timed out. "
            "Please try again."
        )

    if isinstance(exc, APIConnectionError):
        return (
            "Could not connect to the Groq transcription service. "
            "Please check your internet connection and try again."
        )

    if isinstance(exc, BadRequestError):
        return (
            "The audio request could not be processed. "
            "Please try a supported audio file."
        )

    if isinstance(exc, APIStatusError):

        if getattr(exc, "status_code", 0) >= 500:
            return (
                "The transcription service is temporarily unavailable. "
                "Please try again later."
            )

        return (
            "The transcription service returned an error. "
            "Please try again."
        )

    return (
        "An unexpected error occurred while processing "
        "the transcription. Please try again."
    )


# ---------------------------------------------------------
# Transcription
# ---------------------------------------------------------

def transcribe_audio(uploaded_file) -> Dict[str, Any]:
    """
    Transcribe an uploaded or recorded audio file using
    Groq Whisper Large V3.

    Supported languages:

        English
        Urdu
        Roman Urdu
        Urdu + English
    """

    filename = getattr(
        uploaded_file,
        "name",
        "recording.wav",
    )

    base_result = {
        "success": False,
        "text": None,
        "language": None,
        "language_code": None,
        "source": "voice",
        "filename": filename,
        "error": None,
    }

    # -----------------------------------------------------
    # API key
    # -----------------------------------------------------

    if not GROQ_API_KEY:

        base_result["error"] = (
            "Groq API key is not configured. "
            "Please configure GROQ_API_KEY in Streamlit Secrets."
        )

        return base_result

    # -----------------------------------------------------
    # Validate uploaded file
    # -----------------------------------------------------

    try:
        file_bytes = uploaded_file.getvalue()

    except Exception:
        base_result["error"] = (
            "The audio file could not be read. "
            "Please upload or record the audio again."
        )

        return base_result

    if not file_bytes:

        base_result["error"] = (
            "The audio file is empty. "
            "Please record or upload audio containing speech."
        )

        return base_result

    try:

        # -------------------------------------------------
        # Groq client
        # -------------------------------------------------

        client = Groq(
            api_key=GROQ_API_KEY
        )

        # -------------------------------------------------
        # Audio
        # -------------------------------------------------

        file_tuple = (
            filename,
            file_bytes,
        )

        # -------------------------------------------------
        # Whisper
        # -------------------------------------------------

        transcription = (
            client.audio.transcriptions.create(
                file=file_tuple,
                model=MODEL_NAME,
                response_format="verbose_json",
                temperature=0.0,
            )
        )

        # -------------------------------------------------
        # Text
        # -------------------------------------------------

        text = getattr(
            transcription,
            "text",
            "",
        ) or ""

        text = " ".join(
            text.split()
        )

        # -------------------------------------------------
        # Empty transcription
        # -------------------------------------------------

        if not text:

            base_result["error"] = (
                "No speech could be detected in the audio."
            )

            return base_result

        # -------------------------------------------------
        # Whisper language
        # -------------------------------------------------

        language_code = getattr(
            transcription,
            "language",
            None,
        )

        # -------------------------------------------------
        # Final language classification
        # -------------------------------------------------

        final_language = (
            _classify_transcription_language(
                text=text,
                whisper_language_code=language_code,
            )
        )

        # -------------------------------------------------
        # Unsupported language
        # -------------------------------------------------

        if final_language == "Unsupported":

            base_result["text"] = text
            base_result["language_code"] = language_code

            base_result["error"] = (
                "Unsupported language detected. "
                "CivicAgent PK currently supports only "
                "English, Urdu, Roman Urdu, and Urdu + English."
            )

            return base_result

        # -------------------------------------------------
        # Unknown language
        # -------------------------------------------------

        if final_language == "Unknown":

            base_result["error"] = (
                "The language of the audio could not be determined. "
                "Please try recording the complaint again."
            )

            return base_result

        # -------------------------------------------------
        # Success
        # -------------------------------------------------

        base_result.update(
            {
                "success": True,
                "text": text,
                "language": final_language,
                "language_code": language_code,
            }
        )

        return base_result

    # -----------------------------------------------------
    # Groq/API errors
    # -----------------------------------------------------

    except (
        AuthenticationError,
        RateLimitError,
        APITimeoutError,
        APIConnectionError,
        BadRequestError,
        APIStatusError,
    ) as exc:

        base_result["error"] = _handle_groq_error(exc)

        return base_result

    # -----------------------------------------------------
    # Unexpected errors
    # -----------------------------------------------------

    except Exception:

        base_result["error"] = (
            "An unexpected error occurred while processing "
            "the audio. Please try again."
        )

        return base_result