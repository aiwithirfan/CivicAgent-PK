"""
CivicAgent PK — Audio Validation Utilities
"""

from pathlib import Path


# =========================================================
# AUDIO SETTINGS
# =========================================================

MAX_FILE_SIZE_MB = 25

SUPPORTED_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".webm",
    ".mp4",
    ".mpeg",
    ".mpga",
}


SUPPORTED_MIME_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/x-m4a",
    "audio/mp4",
    "audio/webm",
    "audio/mpeg",
}


# =========================================================
# VALIDATION
# =========================================================

def validate_audio_file(
    uploaded_file,
):

    if uploaded_file is None:

        return (
            False,
            "No audio file was provided.",
        )

    filename = getattr(
        uploaded_file,
        "name",
        "recording.wav",
    )

    # -----------------------------------------------------
    # File size
    # -----------------------------------------------------

    try:

        file_size = (
            uploaded_file.getbuffer().nbytes
        )

    except Exception:

        try:

            file_size = len(
                uploaded_file.getvalue()
            )

        except Exception:

            return (
                False,
                "Could not read the audio file.",
            )

    if file_size == 0:

        return (
            False,
            "The audio file is empty.",
        )

    max_size_bytes = (
        MAX_FILE_SIZE_MB
        * 1024
        * 1024
    )

    if file_size > max_size_bytes:

        return (
            False,
            f"Audio file is too large. "
            f"Maximum allowed size is "
            f"{MAX_FILE_SIZE_MB} MB.",
        )

    # -----------------------------------------------------
    # Extension
    # -----------------------------------------------------

    extension = (
        Path(filename)
        .suffix
        .lower()
    )

    if extension not in SUPPORTED_EXTENSIONS:

        return (
            False,
            "Unsupported audio format. "
            "Please use MP3, WAV, M4A or WEBM.",
        )

    # -----------------------------------------------------
    # MIME
    # -----------------------------------------------------

    mime_type = getattr(
        uploaded_file,
        "type",
        None,
    )

    # Browser MIME values can vary.
    # Extension remains the main validation.
    if (
        mime_type
        and mime_type not in SUPPORTED_MIME_TYPES
    ):

        pass

    return True, ""
