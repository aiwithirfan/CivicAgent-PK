"""
CivicAgent PK — Integrated Citizen Complaint Portal
"""
import io
import json
from datetime import datetime
import streamlit as st

st.set_page_config(page_title="CivicAgent PK — Complaint Portal", page_icon="🏛️", layout="wide", initial_sidebar_state="expanded")

try:
    from audio_recorder_streamlit import audio_recorder
    MIC_AVAILABLE = True
    MIC_ERR = None
except Exception as e:
    audio_recorder = None
    MIC_AVAILABLE = False
    MIC_ERR = str(e)

try:
    from transcription import transcribe_audio
    TRANS_AVAILABLE = True
    TRANS_ERR = None
except Exception as e:
    transcribe_audio = None
    TRANS_AVAILABLE = False
    TRANS_ERR = str(e)

try:
    from rag.rag_service import retrieve_context
    RAG_AVAILABLE = True
    RAG_ERR = None
except Exception as e:
    retrieve_context = None
    RAG_AVAILABLE = False
    RAG_ERR = str(e)

try:
    from crew_logic import run_civic_crew
    CREW_AVAILABLE = True
    CREW_ERR = None
except Exception as e:
    run_civic_crew = None
    CREW_AVAILABLE = False
    CREW_ERR = str(e)

try:
    from generate_report import ComplaintRecord, CivicComplaintPDFGenerator
    PDF_AVAILABLE = True
    PDF_ERR = None
except Exception as e:
    ComplaintRecord = None
    CivicComplaintPDFGenerator = None
    PDF_AVAILABLE = False
    PDF_ERR = str(e)

if "history" not in st.session_state: st.session_state.history = []
if "last_response" not in st.session_state: st.session_state.last_response = None
if "audio_bytes" not in st.session_state: st.session_state.audio_bytes = None
if "transcribed_text" not in st.session_state: st.session_state.transcribed_text = ""
if "generated_pdf" not in st.session_state: st.session_state.generated_pdf = None

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
.stApp { background: #F3F5F1; }
.main-title { font-family: 'Lora', serif; font-size: 2.5rem; font-weight: 700; color: #1B2A41; margin-bottom: 0.2rem; }
.subtitle { color: #4B5A66; font-size: 1.05rem; margin-bottom: 1.5rem; }
.section-title { font-family: 'Lora', serif; font-size: 1.35rem; font-weight: 600; color: #1B2A41; margin-top: 1rem; margin-bottom: 0.7rem; }
.result-box { background: #FFFFFF; border: 1px solid #D8DEDA; border-radius: 12px; padding: 20px; margin-top: 15px; }
.footer { text-align: center; color: #4B5A66; margin-top: 35px; padding: 20px; border-top: 1px solid #D8DEDA; }
</style>
""", unsafe_allow_html=True)

def safe_json(val):
    if isinstance(val, dict): return val
    if not val: return {}
    if hasattr(val, "raw"): val = val.raw
    if isinstance(val, str):
        val = val.strip()
        try: return json.loads(val)
        except: pass
        s, e = val.find("{"), val.rfind("}")
        if s != -1 and e != -1 and e > s:
            try: return json.loads(val[s:e+1])
            except: pass
        return {"official_reply_en": val}
    return {"official_reply_en": str(val)}

def normalize_rag(res):
    if not res: return ""
    if isinstance(res, str): return res
    if isinstance(res, list):
        return "\n\n".join([str(i.get("text") or i.get("content") or i) if isinstance(i, dict) else str(i) for i in res])
    if isinstance(res, dict): return str(res.get("context") or res.get("text") or res)
    return str(res)

def extract_transcription(res):
    if not res: return ""
    if isinstance(res, str): return res.strip()
    if isinstance(res, dict):
        for k in ("text", "transcript", "transcription", "detected_text"):
            if res.get(k): return str(res.get(k)).strip()
    return str(res).strip()

def generate_pdf(resp, complaint):
    if not PDF_AVAILABLE: return None
    try:
        ts = datetime.now().strftime("%Y-%m-%d")
        ref = f"CAK-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        rec = ComplaintRecord(
            reference_no=ref, date_submitted=ts, date_processed=ts,
            citizen_name="Valued Citizen", citizen_contact="N/A",
            submission_channel="Web Portal", detected_language="English",
            complaint_text_en=complaint, matched_department=resp.get("department", "Municipal Services"),
            ai_category=resp.get("category", "General"), ai_priority=resp.get("priority", "Medium"),
            official_reply_en=resp.get("official_reply_en", "Received"), status="Forwarded to Department"
        )
        gen = CivicComplaintPDFGenerator()
        path = "temp_report.pdf"
        gen.generate(rec, path)
        with open(path, "rb") as f: return f.read()
    except Exception as e:
        print(f"PDF Error: {e}")
        return None

def process_complaint(complaint):
    complaint = complaint.strip()
    if not complaint: return {"success": False, "error": "Enter a complaint."}
    
    rag = normalize_rag(retrieve_context(complaint) if RAG_AVAILABLE and retrieve_context else "")
    
    if not CREW_AVAILABLE or not run_civic_crew:
        return {"success": False, "error": f"CrewAI unavailable: {CREW_ERR}"}
    
    try:
        try: res = run_civic_crew(complaint_text=complaint, retrieved_policies=rag)
        except TypeError:
            try: res = run_civic_crew(complaint, rag)
            except TypeError: res = run_civic_crew(complaint)
        data = safe_json(res)
    except Exception as e:
        return {"success": False, "error": f"CrewAI failed: {e}"}
    
    data.setdefault("department", "Municipal Services")
    data.setdefault("priority", "Medium")
    data.setdefault("category", "General")
    data.setdefault("official_reply_en", "Your complaint has been received and forwarded for review.")
    data["complaint_text"] = complaint
    data["rag_context"] = rag
    data["success"] = True
    data["processed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return data

st.markdown('<div class="main-title">🏛️ CivicAgent PK</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-Powered Citizen Complaint & Municipal Response System</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ System Status")
    st.success("🎤 Audio Recorder" if MIC_AVAILABLE else "🎤 Unavailable")
    st.success("🗣️ Voice Transcription" if TRANS_AVAILABLE else "🗣️ Unavailable")
    st.success("📚 RAG" if RAG_AVAILABLE else "📚 Unavailable")
    st.success("🤖 CrewAI" if CREW_AVAILABLE else "🤖 Unavailable")
    st.success("📄 PDF Generator" if PDF_AVAILABLE else "📄 Unavailable")
    if st.button("🗑️ Clear Session", use_container_width=True):
        st.session_state.history = []
        st.session_state.last_response = None
        st.session_state.audio_bytes = None
        st.session_state.transcribed_text = ""
        st.session_state.generated_pdf = None
        st.rerun()

st.markdown('<div class="section-title">📝 Submit Your Complaint</div>', unsafe_allow_html=True)
mode = st.radio("Choose input method:", ["⌨️ Text", "🎤 Voice"], horizontal=True)

complaint = ""
if mode == "⌨️ Text":
    complaint = st.text_area("Describe complaint", value=st.session_state.transcribed_text, height=180)
    if complaint: st.session_state.transcribed_text = complaint
else:
    audio = audio_recorder(text="Click to record", recording_color="#B84C3E", neutral_color="#2D6E7E", icon_name="microphone", icon_size="2x")
    if audio:
        st.session_state.audio_bytes = audio
        st.audio(audio, format="audio/wav")
        st.success("Audio recorded.")
        if st.button("🗣️ Convert Voice to Text", use_container_width=True):
            with st.spinner("Transcribing..."):
                try:
                    obj = io.BytesIO(audio) if isinstance(audio, bytes) else audio
                    obj.name = "recording.wav"
                    res = transcribe_audio(obj)
                    txt = extract_transcription(res)
                    if txt:
                        st.session_state.transcribed_text = txt
                        st.success("Converted successfully.")
                        st.text_area("Transcribed", value=txt, height=150, disabled=True)
                    else: st.error("No speech detected.")
                except Exception as e: st.error(f"Failed: {e}")
    if st.session_state.transcribed_text:
        complaint = st.session_state.transcribed_text
        ed = st.text_area("Review / Edit", value=complaint, height=150)
        if ed.strip(): complaint = ed; st.session_state.transcribed_text = ed

st.divider()
if st.button("🚀 Submit Complaint & Generate AI Response", type="primary", use_container_width=True):
    if not complaint.strip(): st.error("Please enter a complaint.")
    else:
        with st.spinner("Analyzing complaint..."): resp = process_complaint(complaint)
        if not resp.get("success"): st.error(resp.get("error", "Error"))
        else:
            st.session_state.last_response = resp
            st.session_state.history.append({"time": resp["processed_at"], "complaint": complaint, "department": resp["department"], "priority": resp["priority"]})
            with st.spinner("Generating PDF..."): st.session_state.generated_pdf = generate_pdf(resp, complaint)

if st.session_state.last_response:
    resp = st.session_state.last_response
    st.markdown('<div class="section-title">📊 AI Analysis & Official Response</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("🏢 Department", resp.get("department"))
    c2.metric("⚠️ Priority", resp.get("priority"))
    c3.metric("📂 Category", resp.get("category"))
    
    st.markdown('<div class="result-box"><h3>📝 Complaint</h3>', unsafe_allow_html=True)
    st.write(resp.get("complaint_text", ""))
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="result-box"><h3>🏛️ Official Response</h3>', unsafe_allow_html=True)
    st.write(resp.get("official_reply_en", ""))
    st.markdown('</div>', unsafe_allow_html=True)
    
    if resp.get("rag_context"):
        with st.expander("📚 Retrieved Policy / RAG Context"): st.write(resp.get("rag_context"))
    
    if st.session_state.generated_pdf:
        st.success("📄 Report generated successfully.")
        st.download_button("⬇️ Download Official PDF Report", data=st.session_state.generated_pdf, file_name="CivicAgent_Report.pdf", mime="application/pdf", use_container_width=True)

if st.session_state.history:
    st.divider()
    st.markdown('<div class="section-title">📜 Complaint History</div>', unsafe_allow_html=True)
    for i, item in enumerate(reversed(st.session_state.history), 1):
        with st.expander(f"Complaint #{i} — {item.get('time', '')}"):
            st.write(f"**Complaint:** {item.get('complaint', '')}")
            st.write(f"**Department:** {item.get('department', '')}")
            st.write(f"**Priority:** {item.get('priority', '')}")

st.markdown('<div class="footer"><strong>CivicAgent PK</strong><br>Intelligent Citizen Complaint Management System</div>', unsafe_allow_html=True)
