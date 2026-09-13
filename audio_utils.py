from pathlib import Path

from config import (
    MAX_FILE_SIZE_MB,
    SUPPORTED_EXTENSIONS,
    SUPPORTED_MIME_TYPES,
)


def validate_audio_file(uploaded_file):
    """
    Validate an uploaded or recorded audio file.

    Returns:
        tuple[bool, str]:
            (True, "") when valid.
            (False, error_message) when invalid.
    """

    if uploaded_file is None:
        return False, "No audio file was provided."

    filename = getattr(uploaded_file, "name", "recording.wav")
    file_size = uploaded_file.getbuffer().nbytes

    if file_size == 0:
        return False, "The audio file is empty."

    max_size_bytes = MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size > max_size_bytes:
        return (
            False,
            f"Audio file is too large. Maximum allowed size is "
            f"{MAX_FILE_SIZE_MB} MB.",
        )

    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        return (
            False,
            "Unsupported audio format. Please use MP3, WAV, M4A, "
            "or WEBM.",
        )

    mime_type = getattr(uploaded_file, "type", None)

    if mime_type and mime_type not in SUPPORTED_MIME_TYPES:
        # Streamlit/browser MIME detection can vary between browsers.
        # Extension validation above remains the primary check.
        pass

    return True, ""