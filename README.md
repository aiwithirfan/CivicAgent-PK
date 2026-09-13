🏛️ CivicAgent PK

AI-Powered Citizen Complaint & Municipal Response System for Pakistan

CivicAgent PK is an AI-powered, multi-agent municipal complaint management system designed to bridge the gap between citizens and local government authorities.

The system allows citizens to submit civic complaints through text or voice in English, Urdu, and Roman Urdu. It automatically analyzes the complaint, retrieves relevant municipal policies using RAG, verifies the complaint through specialized AI agents, and generates an official response and bilingual PDF report.

«🎓 Developed for the HEC-NCEAC & PEC Generative & Agentic AI Training — Cohort 11 Hackathon 1»

---

🚨 Problem Statement

Citizens often face difficulties when reporting everyday municipal problems such as:

- 💧 Water shortages
- 🚰 Water supply issues
- 🚽 Sewerage and drainage problems
- 💡 Broken streetlights
- 🗑️ Waste and sanitation issues
- 🛣️ Road and infrastructure problems
- 🏙️ Other local civic complaints

Traditional complaint processes can be slow, difficult to track, and may require citizens to understand which department or authority is responsible.

CivicAgent PK aims to simplify and automate this process using Agentic AI.

---

💡 Our Solution

CivicAgent PK provides a centralized AI-powered workflow where:

Citizen Complaint → Voice/Text Input → AI Transcription → Complaint Analysis → Policy Retrieval → Policy Verification → Department & Priority → Official Response → PDF Report

The system reduces manual processing and helps generate structured, policy-aware responses for municipal authorities.

---

✨ Key Features

🎙️ 1. Multi-Modal Complaint Intake

Citizens can submit complaints using:

- 📝 Text input
- 🎤 Voice input
- 🇬🇧 English
- 🇵🇰 Urdu
- 🔤 Roman Urdu

---

🗣️ 2. AI Voice Transcription

Voice complaints are converted into text using:

- Groq Whisper API

This allows citizens to report issues naturally without needing to type their complaints.

---

📚 3. RAG-Based Policy Retrieval

The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant information from a local municipal policy knowledge base.

ChromaDB is used as the vector database for storing and retrieving relevant policy information.

This helps the system provide responses based on available policy documents instead of relying only on the LLM's general knowledge.

---

🤖 4. CrewAI Multi-Agent System

CivicAgent PK uses a sequential CrewAI pipeline consisting of three specialized agents.

🔹 Complaint Parser

Responsible for:

- Understanding the citizen's complaint
- Extracting important facts
- Structuring the complaint
- Identifying the main civic issue

🔹 Municipal Policy Auditor

Responsible for:

- Checking relevant municipal policies
- Cross-referencing the complaint with retrieved rules
- Identifying applicable policy information
- Supporting policy-aware decision making

🔹 Official Response Drafter

Responsible for:

- Generating a professional response
- Using the analyzed complaint and policy information
- Producing a citizen-friendly response
- Preparing information for the official report

The response generation uses Groq Llama 3.3.

---

📄 5. Automated Official PDF Reports

CivicAgent PK can generate a professional bilingual English-Urdu PDF report.

The generated report can include:

- 🏛️ Official letterhead
- 🔢 Reference number
- 📋 Complaint details
- 🏢 Relevant department
- 🚨 Priority / urgency
- 🤖 AI-generated official response
- 📚 Relevant legal/policy citations
- 🇬🇧 English content
- 🇵🇰 Urdu content

PDF generation is implemented using ReportLab.

---

🔄 System Workflow

                    👤 CITIZEN
                        │
                        ▼
              ┌──────────────────┐
              │ Voice / Text Input│
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Groq Whisper STT │
              │  (Voice Input)   │
              └────────┬─────────┘
                       │
                       ▼
              ┌──────────────────┐
              │ Complaint Parser │
              │    AI Agent      │
              └────────┬─────────┘
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
     ┌───────────────┐   ┌─────────────────┐
     │   ChromaDB    │   │ Complaint Facts │
     │ Policy / RAG  │   │   & Analysis    │
     └───────┬───────┘   └────────┬────────┘
             │                    │
             └─────────┬──────────┘
                       ▼
             ┌─────────────────────┐
             │ Municipal Policy    │
             │ Auditor Agent       │
             └──────────┬──────────┘
                        │
                        ▼
             ┌─────────────────────┐
             │ Official Response   │
             │ Drafter Agent       │
             │  Groq Llama 3.3     │
             └──────────┬──────────┘
                        │
              ┌─────────┴──────────┐
              ▼                    ▼
       ┌──────────────┐     ┌───────────────┐
       │ Dashboard    │     │ Official PDF  │
       │ Results      │     │ English/Urdu  │
       └──────────────┘     └───────────────┘

---

🧠 AI Architecture

CivicAgent PK combines several modern AI technologies:

Component| Technology
User Interface| Streamlit
Programming Language| Python
LLM| Groq Llama 3.3
Speech-to-Text| Groq Whisper
Agent Framework| CrewAI
RAG| Retrieval-Augmented Generation
Vector Database| ChromaDB
PDF Generation| ReportLab
Environment Management| python-dotenv

---

🛠️ Technology Stack

Frontend

- Streamlit
- Python

AI / LLM

- Groq API
- Llama 3.3

Speech Recognition

- Groq Whisper

Agentic AI

- CrewAI

Retrieval-Augmented Generation

- ChromaDB
- Local policy knowledge base

Document Generation

- ReportLab

Configuration

- python-dotenv

---

🚀 Getting Started

1. Clone the Repository

git clone https://github.com/yourusername/civicagent-pk.git
cd civicagent-pk

---

2. Create a Virtual Environment

Windows

python -m venv venv
venv\Scripts\activate

Linux / macOS

python3 -m venv venv
source venv/bin/activate

---

3. Install Dependencies

pip install -r requirements.txt

---

4. Configure Environment Variables

Create a ".env" file in the root directory:

GROQ_API_KEY=your_groq_api_key_here

«⚠️ Never upload your ".env" file or API keys to GitHub.»

Make sure ".env" is included in ".gitignore":

.env
venv/
__pycache__/
chroma_db/

---

▶️ Run the Application

Start the Streamlit application:

streamlit run app.py

The application will open in your browser.

---

🧪 Example Complaint

Text Input

There is a severe shortage of clean drinking water in our area
for the past three days, and the supply timing is completely irregular.

Voice Input

Hamaray mohallay mein pichlay teen din se gas ki pressure
bilkul khatam hai, baraye meharbani iska hal nikalein.

The system processes the complaint and generates structured results including the relevant department, priority, policy information, and official response.

---

📊 Expected Output

After processing a complaint, the dashboard provides:

Complaint
   ↓
Category / Department
   ↓
Priority / Urgency
   ↓
Relevant Policy
   ↓
AI Analysis
   ↓
Official Response
   ↓
Bilingual PDF Report

---

🌐 Live Demo

🚀 Live Application:
[https://civicagent-pk-2ulotjmrihrrvjc9tzqyqm.streamlit.app/]

---

📚 Project Documentation

Product Requirements Document

📄 PRD:
[https://docs.google.com/document/d/1YZdu5vGHSTZZ5NfbzA3Mi04OfbdIdXfPDBkiAEVXBWY/edit?usp=sharing]

Presentation

📊 Presentation Slides:
[https://docs.google.com/forms/d/e/1FAIpQLScZgb6OnVgxSOdyGQmVoI0j2-u0iBwEH5zrc0GDNTJe__-8Dg/viewform?edit2=2_ABaOnue5Mrc5ZitHnCal021RJsfdq2Lco67nUFyCknOm2eqwbKxRM8IfTUqr8UW_Rw]

Demo Video

🎥 Presentation / Demo Video:
[https://drive.google.com/file/d/1-IquCkODonQRtoAhgQzNOvxZC4M5Qfus/view?usp=sharing]

GitHub Repo Link:
[https://github.com/aiwithirfan/CivicAgent-PK]

---

🔐 Security & Privacy

CivicAgent PK is designed with basic security practices in mind.

- API keys are stored using environment variables.
- ".env" should never be committed to GitHub.
- Sensitive configuration is separated from application code.
- The system should be deployed with appropriate access controls when used with real citizen data.

«Important: This hackathon project is a prototype and should not be considered a replacement for official municipal decision-making or legal advice.»

---

🎯 Project Goals

CivicAgent PK aims to:

- Reduce manual complaint processing
- Improve complaint categorization
- Help identify relevant municipal departments
- Provide policy-aware responses
- Support Urdu and Roman Urdu users
- Improve transparency and accountability
- Automate official documentation
- Demonstrate practical use of Agentic AI in public services

---

🔮 Future Improvements

Future versions of CivicAgent PK could include:

- 🗺️ GPS-based complaint location
- 📍 Interactive complaint mapping
- 📱 Citizen mobile application
- 🔔 SMS / WhatsApp notifications
- 👨‍💼 Dedicated municipal officer dashboard
- 📈 Complaint analytics and statistics
- 🗃️ Centralized government database integration
- 🔐 Citizen authentication
- 📊 Complaint tracking and status updates
- 🏢 Automatic department routing
- 🌐 More Pakistani regional languages
- ☁️ Production-grade cloud deployment
- 🔎 Advanced monitoring and audit logs

---

👥 Team

Team Leader

Irfan Shah

Team Members

- Wajeeha Asad
- Muhammad Kamran Shahzad
- Muhammad Faran
- Shayan Farrukh
- Raiqa Fatima

---

🏆 Hackathon

This project was developed for:

HEC-NCEAC & PEC Generative & Agentic AI Training

Cohort 11 — Hackathon 1

The project demonstrates the practical integration of:

«Generative AI + Agentic AI + RAG + Speech-to-Text + Automated Documentation»

---

📌 Project Highlights

Feature| Status
Text Complaint| ✅
Voice Complaint| ✅
English Support| ✅
Urdu Support| ✅
Roman Urdu Support| ✅
Speech-to-Text| ✅
RAG Policy Retrieval| ✅
ChromaDB| ✅
CrewAI Multi-Agent System| ✅
Complaint Parser Agent| ✅
Policy Auditor Agent| ✅
Response Drafter Agent| ✅
Official Response Generation| ✅
English-Urdu PDF| ✅
Automated Reference Number| ✅
Legal / Policy Citations| ✅
Streamlit Interface| ✅

---

📜 License

This project was developed as a hackathon prototype for educational and demonstration purposes.

Add your preferred open-source license here if the repository will be publicly distributed.

---

🙏 Acknowledgements

Special thanks to:

- HEC
- NCEAC
- PEC
- Generative & Agentic AI Training Program — Cohort 11
- Groq
- CrewAI
- ChromaDB
- Streamlit
- ReportLab

for the technologies, learning environment, and resources that supported this project.

---

⭐ Support the Project

If you find CivicAgent PK useful or interesting, consider giving the repository a ⭐ on GitHub.

Built with ❤️ and AI for smarter civic services in Pakistan 🇵🇰
