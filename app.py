"""
CivicAgent PK — Integrated Citizen Complaint Portal
"""

import io
import json
from datetime import datetime

import streamlit as st


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="CivicAgent PK — Complaint Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# TEAM MODULE IMPORTS
# =========================================================

# ---------------------------------------------------------
# Audio Recorder
# ---------------------------------------------------------

try:
    from audio_recorder_streamlit import audio_recorder

    MIC_AVAILABLE = True
    MIC_IMPORT_ERROR = None

except Exception as e:
    audio_recorder = None
    MIC_AVAILABLE = False
    MIC_IMPORT_ERROR = str(e)


# ---------------------------------------------------------
# Transcription
# ---------------------------------------------------------

try:
    from transcription import transcribe_audio

    TRANSCRIPTION_AVAILABLE = True
    TRANSCRIPTION_IMPORT_ERROR = None

except Exception as e:
    transcribe_audio = None
    TRANSCRIPTION_AVAILABLE = False
    TRANSCRIPTION_IMPORT_ERROR = str(e)


# ---------------------------------------------------------
# RAG
# ---------------------------------------------------------

try:
    from rag.rag_service import retrieve_context

    RAG_AVAILABLE = True
    RAG_IMPORT_ERROR = None

except Exception as e:
    retrieve_context = None
    RAG_AVAILABLE = False
    RAG_IMPORT_ERROR = str(e)


# ---------------------------------------------------------
# CrewAI
# ---------------------------------------------------------

try:
    from crew_logic import run_civic_crew

    CREW_AVAILABLE = True
    CREW_IMPORT_ERROR = None

except Exception as e:
    run_civic_crew = None
    CREW_AVAILABLE = False
    CREW_IMPORT_ERROR = str(e)


# ---------------------------------------------------------
# PDF Generator
# ---------------------------------------------------------

try:
    from generate_report import (
        ComplaintRecord,
        CivicComplaintPDFGenerator,
    )

    PDF_AVAILABLE = True
    PDF_IMPORT_ERROR = None

except Exception as e:
    ComplaintRecord = None
    CivicComplaintPDFGenerator = None
    PDF_AVAILABLE = False
    PDF_IMPORT_ERROR = str(e)


# =========================================================
# SESSION STATE
# =========================================================

if "history" not in st.session_state:
    st.session_state.history = []

if "last_response" not in st.session_state:
    st.session_state.last_response = None

if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None

if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""

if "generated_pdf" not in st.session_state:
    st.session_state.generated_pdf = None


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    @import url(
        'https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap'
    );

    :root {
        --ink: #1B2A41;
        --teal: #2D6E7E;
        --teal-dark: #204F5B;
        --paper: #F3F5F1;
        --paper-alt: #FFFFFF;
        --amber: #B8752E;
        --green: #3E7D5A;
        --rust: #B84C3E;
        --slate: #4B5A66;
        --border: #D8DEDA;
    }

    html,
    body,
    [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    .stApp {
        background: var(--paper);
    }

    .main-title {
        font-family: 'Lora', serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--ink);
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: var(--slate);
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }

    .section-title {
        font-family: 'Lora', serif;
        font-size: 1.35rem;
        font-weight: 600;
        color: var(--ink);
        margin-top: 1rem;
        margin-bottom: 0.7rem;
    }

    .info-box {
        background: var(--paper-alt);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
    }

    .result-box {
        background: var(--paper-alt);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
    }

    .status-good {
        color: var(--green);
        font-weight: 600;
    }

    .status-bad {
        color: var(--rust);
        font-weight: 600;
    }

    .footer {
        text-align: center;
        color: var(--slate);
        margin-top: 35px;
        padding: 20px;
        border-top: 1px solid var(--border);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def safe_json(value):
    """Convert CrewAI result into a Python dictionary."""

    if isinstance(value, dict):
        return value

    if value is None:
        return {}

    if hasattr(value, "raw"):
        value = value.raw

    if isinstance(value, str):
        text = value.strip()

        try:
            return json.loads(text)
        except Exception:
            pass

        # Try extracting JSON from surrounding text
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                pass

        return {
            "official_reply_en": text
        }

    return {
        "official_reply_en": str(value)
    }


def normalize_rag_result(result):
    """Normalize different RAG return formats."""

    if result is None:
        return ""

    if isinstance(result, str):
        return result

    if isinstance(result, list):
        parts = []

        for item in result:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = (
                    item.get("text")
                    or item.get("content")
                    or item.get("document")
                    or str(item)
                )
                parts.append(str(text))
            else:
                parts.append(str(item))

        return "\n\n".join(parts)

    if isinstance(result, dict):
        return (
            result.get("context")
            or result.get("text")
            or result.get("content")
            or str(result)
        )

    return str(result)


def extract_transcription(result):
    """Extract transcript text from different transcription return formats."""

    if result is None:
        return ""

    if isinstance(result, str):
        return result.strip()

    if isinstance(result, dict):
        for key in (
            "text",
            "transcript",
            "transcription",
            "detected_text",
            "cleaned_text",
        ):
            value = result.get(key)

            if value:
                return str(value).strip()

    return str(result).strip()


def generate_pdf(response_data, complaint_text):
    """Generate PDF when the team PDF module is available."""

    if not PDF_AVAILABLE:
        return None

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        ref_no = f"CAK-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        department = response_data.get(
            "department",
            "Government of Pakistan — Municipal Services"
        )

        priority = response_data.get(
            "priority",
            "Medium"
        )

        category = response_data.get(
            "category",
            "General Civic Complaint"
        )

        official_reply = response_data.get(
            "official_reply_en",
            response_data.get(
                "official_reply",
                "Complaint received and forwarded for review."
            )
        )

        # Create record matching ComplaintRecord structure in generate_report.py
        record = ComplaintRecord(
            reference_no=ref_no,
            date_submitted=timestamp,
            date_processed=timestamp,
            citizen_name="Valued Citizen",
            citizen_contact="N/A",
            submission_channel="Web Portal",
            detected_language="English",
            complaint_text_en=complaint_text,
            matched_department=department,
            ai_category=category,
            ai_priority=priority,
            official_reply_en=official_reply,
            status="Forwarded to Department",
        )

        generator = CivicComplaintPDFGenerator()
        out_path = "temp_complaint_report.pdf"
        generator.generate(record, out_path)

        with open(out_path, "rb") as f:
            pdf_bytes = f.read()

        return pdf_bytes

    except Exception as e:
        print(f"PDF Generation Error: {e}")
        return None


def process_complaint(complaint_text):
    """Complete complaint-processing pipeline."""

    complaint_text = complaint_text.strip()

    if not complaint_text:
        return {
            "success": False,
            "error": "Please enter a complaint first."
        }

    # -----------------------------------------------------
    # STEP 1 — RAG
    # -----------------------------------------------------

    rag_context = ""

    if RAG_AVAILABLE and retrieve_context:

        try:
            rag_result = retrieve_context(complaint_text)
            rag_context = normalize_rag_result(rag_result)

        except Exception as e:
            rag_context = ""
            st.warning(
                f"RAG could not be used. Continuing without policy context. "
                f"Reason: {e}"
            )

    # -----------------------------------------------------
    # STEP 2 — CREWAI
    # -----------------------------------------------------

    if not CREW_AVAILABLE or run_civic_crew is None:
        return {
            "success": False,
            "error": (
                "CrewAI module could not be loaded.\n\n"
                f"{CREW_IMPORT_ERROR}"
            )
        }

    try:

        # Try the most complete interface first.
        try:
            crew_result = run_civic_crew(
                complaint_text=complaint_text,
                retrieved_policies=rag_context,
            )

        except TypeError:

            # Compatibility with older crew_logic.py
            try:
                crew_result = run_civic_crew(
                    complaint_text,
                    rag_context,
                )

            except TypeError:

                crew_result = run_civic_crew(
                    complaint_text
                )

        result = safe_json(crew_result)

    except Exception as e:

        return {
            "success": False,
            "error": f"CrewAI processing failed:\n{e}"
        }

    # -----------------------------------------------------
    # STEP 3 — DEFAULT VALUES
    # -----------------------------------------------------

    result.setdefault(
        "department",
        "Municipal Administration"
    )

    result.setdefault(
        "priority",
        "Medium"
    )

    result.setdefault(
        "category",
        "General Civic Complaint"
    )

    result.setdefault(
        "official_reply_en",
        "Your complaint has been received and forwarded to the relevant municipal department for review."
    )

    result["complaint_text"] = complaint_text
    result["rag_context"] = rag_context
    result["success"] = True
    result["processed_at"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return result


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🏛️ CivicAgent PK</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    'AI-Powered Citizen Complaint & Municipal Response System'
    '</div>',
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ System Status")

    if MIC_AVAILABLE:
        st.success("🎤 Audio Recorder: Available")
    else:
        st.error("🎤 Audio Recorder: Unavailable")
        if MIC_IMPORT_ERROR:
            st.caption(MIC_IMPORT_ERROR)

    if TRANSCRIPTION_AVAILABLE:
        st.success("🗣️ Voice Transcription: Available")
    else:
        st.error("🗣️ Voice Transcription: Unavailable")
        if TRANSCRIPTION_IMPORT_ERROR:
            st.caption(
                f"Error: {TRANSCRIPTION_IMPORT_ERROR}"
            )

    if RAG_AVAILABLE:
        st.success("📚 RAG: Available")
    else:
        st.warning("📚 RAG: Unavailable")
        if RAG_IMPORT_ERROR:
            st.caption(RAG_IMPORT_ERROR)

    if CREW_AVAILABLE:
        st.success("🤖 CrewAI: Available")
    else:
        st.error("🤖 CrewAI: Unavailable")
        if CREW_IMPORT_ERROR:
            st.caption(CREW_IMPORT_ERROR)

    if PDF_AVAILABLE:
        st.success("📄 PDF Generator: Available")
    else:
        st.warning("📄 PDF Generator: Unavailable")
        if PDF_IMPORT_ERROR:
            st.caption(PDF_IMPORT_ERROR)

    st.divider()

    st.markdown(
        """
        **CivicAgent PK**

        Citizen complaint →  
        Voice/Text processing →  
        RAG policy retrieval →  
        Multi-Agent AI →  
        Official response →  
        PDF report
        """
    )

    if st.button("🗑️ Clear Session", use_container_width=True):
        st.session_state.history = []
        st.session_state.last_response = None
        st.session_state.audio_bytes = None
        st.session_state.transcribed_text = ""
        st.session_state.generated_pdf = None
        st.rerun()


# =========================================================
# MAIN INPUT AREA
# =========================================================

st.markdown(
    '<div class="section-title">📝 Submit Your Complaint</div>',
    unsafe_allow_html=True,
)

input_mode = st.radio(
    "Choose complaint input method:",
    ["⌨️ Text", "🎤 Voice"],
    horizontal=True,
)


# =========================================================
# TEXT INPUT
# =========================================================

complaint_text = ""

if input_mode == "⌨️ Text":

    complaint_text = st.text_area(
        "Describe your civic complaint",
        value=st.session_state.transcribed_text,
        height=180,
        placeholder=(
            "Example: The street lights in our area have not been "
            "working for the last two weeks."
        ),
        help="Write your complaint in English, Urdu, or Roman Urdu.",
    )

    if complaint_text:
        st.session_state.transcribed_text = complaint_text


# =========================================================
# VOICE INPUT
# =========================================================

else:

    st.write(
        "Press the microphone button and speak your complaint."
    )

    if not MIC_AVAILABLE:

        st.error(
            "🎤 Audio recorder is not available."
        )

        if MIC_IMPORT_ERROR:
            st.code(
                MIC_IMPORT_ERROR,
                language="text"
            )

    else:

        audio_data = audio_recorder(
            text="Click to record",
            recording_color="#B84C3E",
            neutral_color="#2D6E7E",
            icon_name="microphone",
            icon_size="2x",
        )

        if audio_data:

            st.session_state.audio_bytes = audio_data

            st.audio(
                audio_data,
                format="audio/wav"
            )

            st.success(
                "Audio recorded successfully."
            )

            # -------------------------------------------------
            # Transcription
            # -------------------------------------------------

            if not TRANSCRIPTION_AVAILABLE:

                st.error(
                    "🗣️ Audio transcription module could not be loaded."
                )

                if TRANSCRIPTION_IMPORT_ERROR:
                    st.code(
                        TRANSCRIPTION_IMPORT_ERROR,
                        language="text"
                    )

            elif st.button(
                "🗣️ Convert Voice to Text",
                use_container_width=True,
            ):

                with st.spinner(
                    "Transcribing your complaint..."
                ):

                    try:

                        result = transcribe_audio(
                            audio_data
                        )

                        transcript = extract_transcription(
                            result
                        )

                        if transcript:

                            st.session_state.transcribed_text = transcript

                            st.success(
                                "Voice converted to text successfully."
                            )

                            st.text_area(
                                "Transcribed Complaint",
                                value=transcript,
                                height=150,
                                disabled=True,
                            )

                        else:

                            st.error(
                                "No text could be extracted from the audio."
                            )

                    except Exception as e:

                        st.error(
                            f"Voice transcription failed: {e}"
                        )

                        st.exception(e)

            if st.session_state.transcribed_text:

                complaint_text = st.session_state.transcribed_text

                st.info(
                    "Transcribed complaint is ready for processing."
                )

                edited_text = st.text_area(
                    "Review / Edit Complaint",
                    value=complaint_text,
                    height=150,
                )

                if edited_text.strip():
                    complaint_text = edited_text
                    st.session_state.transcribed_text = edited_text


# =========================================================
# PROCESS BUTTON
# =========================================================

st.divider()

submit = st.button(
    "🚀 Submit Complaint & Generate AI Response",
    type="primary",
    use_container_width=True,
)


# =========================================================
# PROCESS COMPLAINT
# =========================================================

if submit:

    if not complaint_text.strip():

        st.error(
            "Please enter a complaint or record a voice complaint first."
        )

    else:

        with st.spinner(
            "CivicAgent is analyzing your complaint..."
        ):

            response = process_complaint(
                complaint_text
            )

        if not response.get("success"):

            st.error(
                response.get(
                    "error",
                    "Unable to process complaint."
                )
            )

        else:

            st.session_state.last_response = response

            st.session_state.history.append(
                {
                    "time": response.get(
                        "processed_at",
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ),
                    "complaint": complaint_text,
                    "department": response.get(
                        "department",
                        "Unknown"
                    ),
                    "priority": response.get(
                        "priority",
                        "Medium"
                    ),
                }
            )

            # -------------------------------------------------
            # Generate PDF
            # -------------------------------------------------

            with st.spinner(
                "Generating official PDF report..."
            ):

                pdf_bytes = generate_pdf(
                    response,
                    complaint_text,
                )

            if pdf_bytes:

                st.session_state.generated_pdf = pdf_bytes

            else:

                st.session_state.generated_pdf = None


# =========================================================
# DISPLAY RESULT
# =========================================================

if st.session_state.last_response:

    response = st.session_state.last_response

    st.markdown(
        '<div class="section-title">📊 AI Analysis & Official Response</div>',
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # Key Information
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "🏢 Department",
            response.get(
                "department",
                "Unknown"
            ),
        )

    with col2:

        st.metric(
            "⚠️ Priority",
            response.get(
                "priority",
                "Medium"
            ),
        )

    with col3:

        st.metric(
            "📂 Category",
            response.get(
                "category",
                "General"
            ),
        )

    # -----------------------------------------------------
    # Complaint
    # -----------------------------------------------------

    st.markdown(
        '<div class="result-box">',
        unsafe_allow_html=True,
    )

    st.subheader("📝 Complaint")

    st.write(
        response.get(
            "complaint_text",
            ""
        )
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # Official Response
    # -----------------------------------------------------

    st.markdown(
        '<div class="result-box">',
        unsafe_allow_html=True,
    )

    st.subheader("🏛️ Official Response")

    st.write(
        response.get(
            "official_reply_en",
            "No official response generated."
        )
    )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )

    # -----------------------------------------------------
    # Urdu Response if available
    # -----------------------------------------------------

    urdu_reply = (
        response.get("official_reply_ur")
        or response.get("urdu_reply")
        or response.get("response_ur")
    )

    if urdu_reply:

        st.markdown(
            '<div class="result-box">',
            unsafe_allow_html=True,
        )

        st.subheader("🇵🇰 Urdu Response")

        st.write(urdu_reply)

        st.markdown(
            "</div>",
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------
    # RAG Context
    # -----------------------------------------------------

    rag_context = response.get(
        "rag_context",
        ""
    )

    if rag_context:

        with st.expander(
            "📚 Retrieved Policy / RAG Context"
        ):

            st.write(rag_context)

    # -----------------------------------------------------
    # Raw AI Result
    # -----------------------------------------------------

    with st.expander(
        "🔍 Technical AI Output"
    ):

        st.json(
            {
                key: value
                for key, value in response.items()
                if key != "rag_context"
            }
        )

    # -----------------------------------------------------
    # PDF Download
    # -----------------------------------------------------

    if st.session_state.generated_pdf:

        st.success(
            "📄 Official complaint report generated successfully."
        )

        st.download_button(
            label="⬇️ Download Official PDF Report",
            data=st.session_state.generated_pdf,
            file_name=(
                "CivicAgent_PK_Complaint_Report.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
        )

    elif PDF_AVAILABLE:

        st.warning(
            "PDF generator is available, but no PDF was returned. "
            "Check generate_report.py interface."
        )

    else:

        st.info(
            "PDF generation module is currently unavailable."
        )


# =========================================================
# HISTORY
# =========================================================

if st.session_state.history:

    st.divider()

    st.markdown(
        '<div class="section-title">📜 Complaint History</div>',
        unsafe_allow_html=True,
    )

    for index, item in enumerate(
        reversed(st.session_state.history),
        start=1,
    ):

        with st.expander(
            f"Complaint #{index} — "
            f"{item.get('time', '')}"
        ):

            st.write(
                f"**Complaint:** {item.get('complaint', '')}"
            )

            st.write(
                f"**Department:** {item.get('department', '')}"
            )

            st.write(
                f"**Priority:** {item.get('priority', '')}"
            )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        <strong>CivicAgent PK</strong><br>
        Intelligent Citizen Complaint Management System<br>
        Agentic AI • RAG • Voice Processing • Municipal Automation
    </div>
    """,
    unsafe_allow_html=True,
)
