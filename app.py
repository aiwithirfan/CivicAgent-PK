"""
CivicAgent PK — Integrated Citizen Complaint Portal
"""

import io
import os
import time
from datetime import datetime
import streamlit as st

# --- Team Modules Imports ---
try:
    from audio_recorder_streamlit import audio_recorder
    MIC_AVAILABLE = True
except ImportError:
    MIC_AVAILABLE = False

try:
    from transcription import transcribe_audio
except ImportError:
    transcribe_audio = None

# Wajeeha's RAG for fetching policies
try:
    from rag.rag_service import retrieve_context
except ImportError:
    retrieve_context = None

# Irfan Shah's CrewAI Logic for Decision Making
try:
    from crew_logic import run_civic_crew
except ImportError:
    run_civic_crew = None

try:
    from generate_report import ComplaintRecord, CivicComplaintPDFGenerator
except ImportError:
    ComplaintRecord, CivicComplaintPDFGenerator = None, None


# --- Page Setup ---
st.set_page_config(
    page_title="CivicAgent PK — Complaint Portal",
    page_icon="🏛",
    layout="wide",
    initial_sidebar_state="expanded",
)

if "history" not in st.session_state:
    st.session_state.history = []
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None


# --- Styling ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
    :root {
        --ink: #1B2A41; --teal: #2D6E7E; --teal-dark: #204F5B;
        --paper: #F3F5F1; --paper-alt: #FFFFFF; --amber: #B8752E;
        --green: #3E7D5A; --rust: #B84C3E; --slate: #4B5A66; --border: #D8DEDA;
    }
    html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; color: var(--ink); }
    .stApp { background: var(--paper); }
    .masthead { display: flex; justify-content: space-between; align-items: flex-end; border-bottom: 2px solid var(--ink); padding-bottom: 18px; margin-bottom: 28px; }
    .masthead-title { font-family: 'Lora', serif; font-weight: 600; font-size: 2.05rem; color: var(--ink); margin: 0; line-height: 1.15; }
    .panel { background: var(--paper-alt); border: 1px solid var(--border); border-left: 4px solid var(--teal); padding: 26px 28px; margin-bottom: 20px; }
    .ticket { background: var(--paper-alt); border: 1px solid var(--border); border-left: 4px solid var(--amber); padding: 26px 28px; }
    .ticket.resolved-style { border-left-color: var(--green); }
    .stButton > button { background: var(--ink); color: var(--paper-alt); border: none; border-radius: 2px; padding: 0.55rem 1.4rem; font-weight: 500; }
    .stButton > button:hover { background: var(--teal-dark); color: var(--paper-alt); }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Integrated AI Logic ---
def submit_complaint_integrated(text: str, source: str):
    category = "General"
    urgency = "Standard"
    response_text = "Complaint has been forwarded to the relevant department."
    department = "Municipal Services"

    with st.spinner("AI is analyzing policies and drafting a response..."):
        # 1. Get Policies from Wajeeha & Raiqa's RAG DB
        retrieved_policies = []
        if retrieve_context:
            try:
                context = retrieve_context(complaint=text, top_k=2)
                retrieved_policies = context.get("retrieved_policies", [])
            except Exception as e:
                st.error(f"RAG Error: {e}")

        # 2. Irfan Shah's CrewAI Agent Decision Making
        if run_civic_crew:
            try:
                analysis = run_civic_crew(text, retrieved_policies)
                category = analysis.get("category", category)
                urgency = analysis.get("priority", urgency)
                response_text = analysis.get("official_reply_en", response_text)
                department = analysis.get("department", department)
            except Exception as e:
                st.error(f"CrewAI Logic Error: {e}")

        ticket_id = f"CAK-2026-{len(st.session_state.history) + 1042}"
        date_now = datetime.now().strftime("%Y-%m-%d")

        record_data = {
            "id": ticket_id,
            "text": text,
            "source": source,
            "category": category,
            "urgency": urgency,
            "response": response_text,
            "time": datetime.now().strftime("%b %d, %H:%M"),
        }

        # 3. PDF Generation (Shayan)
        if CivicComplaintPDFGenerator and ComplaintRecord:
            try:
                pdf_record = ComplaintRecord(
                    reference_no=ticket_id,
                    date_submitted=date_now,
                    date_processed=date_now,
                    citizen_name="Anonymous Citizen",
                    citizen_contact="Not Provided",
                    submission_channel=source,
                    detected_language="Mixed",
                    complaint_text_en=text,
                    matched_department=department,
                    ai_category=category,
                    ai_priority=urgency,
                    official_reply_en=response_text
                )
                pdf_filename = f"{ticket_id}_Report.pdf"
                generator = CivicComplaintPDFGenerator()
                generator.generate(pdf_record, pdf_filename)
                record_data["pdf_file"] = pdf_filename
            except Exception as e:
                st.error(f"PDF Generation Error: {e}")

        st.session_state.history.insert(0, record_data)
        st.session_state.last_response = record_data


# --- Sidebar ---
with st.sidebar:
    st.markdown("### CivicAgent PK")
    st.caption("AI-Powered Municipal Helper")
    st.markdown("---")
    st.markdown("**Look up a ticket**")
    lookup_id = st.text_input("Ticket ID", placeholder="e.g. CAK-2026-1042", label_visibility="collapsed")
    if lookup_id:
        match = next((r for r in st.session_state.history if r["id"].lower() == lookup_id.lower()), None)
        if match:
            st.success(f"{match['id']} — {match['category']}")
            st.write(match["response"])
        else:
            st.warning("No ticket found with that ID.")

# --- Masthead ---
st.markdown(
    f"""
    <div class="masthead">
        <div>
            <p class="masthead-title">CivicAgent PK</p>
            <p style="color:var(--slate); margin-top:4px;">File a complaint by typing or speaking. AI will process it.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --- Main Layout ---
col_left, col_right = st.columns([1.05, 1], gap="large")

with col_left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("### Tell us what's wrong")
    
    complaint_text = st.text_area("Complaint", placeholder="Type your issue here...", height=140, label_visibility="collapsed")
    st.markdown("&nbsp;", unsafe_allow_html=True)

    if MIC_AVAILABLE:
        mic_col, mic_label_col = st.columns([0.15, 0.85])
        with mic_col:
            audio_bytes = audio_recorder(text="", icon_size="2x", pause_threshold=3.0)
        with mic_label_col:
            st.markdown('<div style="padding-top:14px; color:#4B5A66; font-size:0.88rem;">Tap to record a voice complaint.</div>', unsafe_allow_html=True)
        if audio_bytes:
            st.session_state.audio_bytes = audio_bytes
            st.audio(audio_bytes, format="audio/wav")

    submitted = st.button("Submit complaint")

    if submitted:
        final_text = complaint_text.strip()
        source = "Text"

        if not final_text and st.session_state.audio_bytes:
            # Kamran's Audio Processing
            if transcribe_audio:
                audio_file = io.BytesIO(st.session_state.audio_bytes)
                audio_file.name = "recording.wav"
                
                with st.spinner("Transcribing your voice with Whisper API..."):
                    try:
                        transcription_result = transcribe_audio(audio_file)
                    except Exception as e:
                        transcription_result = {"success": False, "error": str(e)}
                    
                if transcription_result and transcription_result.get("success"):
                    final_text = transcription_result["text"]
                    lang = transcription_result.get("language", "Unknown")
                    source = f"Voice ({lang})"
                    st.success("Audio transcribed successfully!")
                else:
                    err_msg = transcription_result.get("error", "Transcription failed.") if transcription_result else "Audio transcription service unavailable."
                    st.error(err_msg)
                    final_text = None
            else:
                st.error("Audio module is not available.")

        if not final_text:
            st.warning("Please type your complaint or record a voice message first.")
        else:
            submit_complaint_integrated(final_text, source)
            st.session_state.audio_bytes = None

    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    record = st.session_state.last_response

    if record is None:
        st.markdown('<div class="ticket">', unsafe_allow_html=True)
        st.markdown("### Response")
        st.markdown('<p style="color:#4B5A66;">Once you submit a complaint, the AI response will appear here.</p>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="ticket resolved-style">', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size: 0.82rem; color: var(--slate); margin-bottom: 6px;">Ticket {record["id"]} · {record["time"]}</div>', unsafe_allow_html=True)
        st.markdown("### AI Response")
        st.markdown(f'<p style="color:var(--slate); font-size:0.88rem;"><b>Category:</b> {record["category"]} | <b>Priority:</b> {record["urgency"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:var(--slate); font-size:0.88rem;"><b>Original Complaint:</b></p>', unsafe_allow_html=True)
        st.markdown(f'<p style="margin-top:-8px;">{record["text"]}</p>', unsafe_allow_html=True)
        st.markdown('<p style="color:var(--slate); font-size:0.88rem; margin-top:16px;"><b>Official Reply:</b></p>', unsafe_allow_html=True)
        st.markdown(f'<p style="margin-top:-8px;">{record["response"]}</p>', unsafe_allow_html=True)
        
        if "pdf_file" in record and os.path.exists(record["pdf_file"]):
            st.markdown("---")
            with open(record["pdf_file"], "rb") as pdf_file:
                st.download_button(
                    label="📄 Download Official PDF Report",
                    data=pdf_file,
                    file_name=record["pdf_file"],
                    mime="application/pdf"
                )
        st.markdown("</div>", unsafe_allow_html=True)
