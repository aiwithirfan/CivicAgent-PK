"""
CivicAgent PK — Integrated Citizen Complaint Portal
"""

import io
import os
from datetime import datetime

import streamlit as st


# =========================================================
# TEAM MODULE IMPORTS
# =========================================================

# Microphone recorder
try:
    from audio_recorder_streamlit import audio_recorder
    MIC_AVAILABLE = True
    MIC_IMPORT_ERROR = None
except Exception as e:
    audio_recorder = None
    MIC_AVAILABLE = False
    MIC_IMPORT_ERROR = str(e)


# Whisper / Voice-to-Text
try:
    from transcription import transcribe_audio
    TRANSCRIPTION_AVAILABLE = True
    TRANSCRIPTION_IMPORT_ERROR = None
except Exception as e:
    transcribe_audio = None
    TRANSCRIPTION_AVAILABLE = False
    TRANSCRIPTION_IMPORT_ERROR = str(e)


# Wajeeha's RAG
try:
    from rag.rag_service import retrieve_context
    RAG_AVAILABLE = True
    RAG_IMPORT_ERROR = None
except Exception as e:
    retrieve_context = None
    RAG_AVAILABLE = False
    RAG_IMPORT_ERROR = str(e)


# Irfan's CrewAI
try:
    from crew_logic import run_civic_crew
    CREW_AVAILABLE = True
    CREW_IMPORT_ERROR = None
except Exception as e:
    run_civic_crew = None
    CREW_AVAILABLE = False
    CREW_IMPORT_ERROR = str(e)


# Shayan's PDF Generator
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
# PAGE SETUP
# =========================================================

st.set_page_config(
    page_title="CivicAgent PK — Complaint Portal",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# SESSION STATE
# =========================================================

if "history" not in st.session_state:
    st.session_state.history = []

if "last_response" not in st.session_state:
    st.session_state.last_response = None

if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None


# =========================================================
# STYLING
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
        color: var(--ink);
    }

    .stApp {
        background: var(--paper);
    }

    .masthead {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        border-bottom: 2px solid var(--ink);
        padding-bottom: 18px;
        margin-bottom: 28px;
    }

    .masthead-title {
        font-family: 'Lora', serif;
        font-weight: 600;
        font-size: 2.05rem;
        color: var(--ink);
        margin: 0;
        line-height: 1.15;
    }
