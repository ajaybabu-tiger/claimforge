# ClaimForge — Turn Claim Denials into Evidence-Backed Appeals

> **VISTERA 2026 National Hackathon Project**  
> *AI-Assisted Healthcare Insurance Claim Verification & Appeal Preparation Platform*

---

## 1. Problem & Solution Overview

### The Problem
Every year, over 15% of legitimate medical insurance claims in the United States and global healthcare systems are denied. Common denial reasons include:
- Alleged lack of pre-authorization (Code `CO-197`)
- Allegations that care was experimental or not medically necessary (Code `CO-50`)
- Out-of-network balance billing disputes (Code `PR-204`)
- Unmatched clinical dates, clerical errors, or document alteration artifacts

Patients, billing specialists, and clinical advocates often lack the hours required to cross-reference itemized hospital ledgers, clinical discharge summaries, and diagnostic reports to construct compliant, statutory appeals.

### The Solution: ClaimForge
ClaimForge is an intelligent decision-support platform designed to streamline claim verification and appeal generation:
1. **Case Intake**: Collects claim reference, patient identification, insurer, billed amounts, and stated rejection reasons.
2. **Multi-Document Extraction**: Ingests itemized bills, operative/discharge notes, MRI/radiology reports, prescriptions, and EOB notices using PyMuPDF and regex entity recognizers.
3. **Cross-Document Consistency**: Compares dates, amounts, ICD-10 diagnostic codes, CPT procedure codes, and provider identifications across all files.
4. **Document Integrity Checks**: Scans for arithmetic modifications (sum of line items vs stated invoice total) and metadata/font diversity anomalies.
5. **Appeal Readiness Score (0–100)**: Evaluates Evidence Completeness, Cross-Doc Consistency, Rejection Rebuttal Strength, and Document Integrity.
6. **Statutory Rebuttal Analysis**: Automatically matches clinical records against federal regulations (e.g. **EMTALA 42 U.S.C. § 1395dd**, **ACA § 2719A**, **No Surprises Act**, **ERISA § 1133**).
7. **Human Reviewer Sign-Off**: Enables human reviewers to confirm or dismiss findings, input clinical notes, and approve drafts.
8. **Audit-Ready PDF Packet Export**: Generates a professional, letterhead-styled PDF appeal packet with itemized documentary exhibits.

> **Responsible AI Principle:** ClaimForge is a human decision-support system, not an autonomous fraud detector or insurance approval system. It assists human judgment and never fabricates facts or accuses parties of fraud.

---

## 2. Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, Lucide Icons.
- **Backend**: Python 3.11/3.13, FastAPI, Pydantic V2, SQLAlchemy 2.0 (AsyncIO), ReportLab, PyMuPDF (`fitz`), Pillow.
- **Database & Storage**:
  - **Local Development Mode**: SQLite (`aiosqlite`) + local `/uploads` directory. Zero external dependencies or paid APIs required for local testing.
  - **Production/Cloud Mode**: Supabase PostgreSQL with Row Level Security (RLS) + Supabase Storage private buckets.
- **AI Integration**: Provider-independent adapter supporting Gemini, OpenAI, and Anthropic, with an explainable, deterministic rule-based analysis engine fallback.

---

## 3. Project Structure

```
claimforge/
├── backend/
│   ├── app/
│   │   ├── api/             # REST endpoints (health, claims, documents, analysis, readiness, appeals, demo)
│   │   ├── core/            # Config, database engine, CORS
│   │   ├── models/          # SQLAlchemy ORM models (Claim, Document, Finding, Appeal, AnalysisRun)
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── repositories/    # Database query access layer
│   │   └── services/        # PyMuPDF extractor, analysis engine, readiness service, appeal generator, PDF exporter
│   ├── tests/               # Pytest automated test suite
│   ├── uploads/             # Private document storage
│   ├── requirements.txt
│   └── run_server.py        # Backend server launcher
├── frontend/
│   ├── src/
│   │   ├── app/             # App Router pages (/, /dashboard, /claims/new, /claims/[id], /claims/[id]/appeal, /demo)
│   │   ├── components/      # Reusable UI components (Navbar, Footer, ReadinessGauge, FindingsList, CrossDocMatrix)
│   │   └── lib/             # Typed API client, TypeScript types, badge/formatting helpers
│   ├── package.json
│   └── tailwind.config.js
├── database/
│   ├── migrations/          # 001_initial_schema.sql (SQLite & PostgreSQL compatible)
│   └── supabase_setup.sql   # Supabase RLS policies and storage bucket setup
├── docs/
│   ├── architecture.md      # Comprehensive architecture specification
│   ├── api.md               # REST API reference
│   └── demo-guide.md        # Step-by-step judge walkthrough script
├── docker-compose.yml       # Docker container orchestration
├── .env.example             # Environment configuration template
└── README.md
```

---

## 4. Quick Start Commands

### Prerequisites
- Python 3.10+ (Python 3.11/3.13 tested)
- Node.js 18+ and npm

### 1. Start the Backend
```bash
# In project root
python -m venv venv
.\venv\Scripts\activate   # On Windows (or source venv/bin/activate on Linux/Mac)
pip install -r backend/requirements.txt

# Run backend API server (runs on http://127.0.0.1:8000)
python backend/run_server.py
```
- Interactive API Docs: `http://127.0.0.1:8000/docs`
- Health Check: `http://127.0.0.1:8000/health`

### 2. Start the Frontend
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```
- Open `http://localhost:3000` in your web browser.

### Active Exploration Links
| Service | Link |
| :--- | :--- |
| **ClaimForge Web Application** | [http://localhost:3000](http://localhost:3000) |
| **Live Claims Dashboard** | [http://localhost:3000/dashboard](http://localhost:3000/dashboard) |
| **Interactive Demo Cases** | [http://localhost:3000/demo](http://localhost:3000/demo) |
| **Interactive API Documentation** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) |
| **Backend Health Status** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) |

---

## 5. Deployment Options (Deploying Total Folder)

ClaimForge is configured so that uploading or pushing the entire project folder to any cloud platform works out-of-the-box:

- **1-Click Render**: Upload/push repo and connect via [render.yaml](file:///c:/Users/Ajay%20Babu/OneDrive/Desktop/claimforger1/render.yaml) blueprint or Docker environment.
- **1-Click Railway**: Deploy directly from Git; automatically detected via root [Dockerfile](file:///c:/Users/Ajay%20Babu/OneDrive/Desktop/claimforger1/Dockerfile) and [railway.json](file:///c:/Users/Ajay%20Babu/OneDrive/Desktop/claimforger1/railway.json).
- **Docker Compose**: `docker compose up -d --build` (launches frontend on `:3000` and backend on `:8000`).
- **Single Container Docker**: `docker build -t claimforge . && docker run -p 3000:3000 claimforge`
- **Clean ZIP Upload**: Run `python package_project.py` or `.\package_project.ps1` to produce `claimforge_deployment.zip` (clean 400 KB archive excluding OS virtualenvs and node_modules).
- See detailed instructions in [DEPLOYMENT.md](file:///c:/Users/Ajay%20Babu/OneDrive/Desktop/claimforger1/DEPLOYMENT.md).

---

## 6. Automated Tests

The backend test suite verifies the complete pipeline:
- Health check verification
- Claim lifecycle (CRUD, filters, updates)
- Document upload and PyMuPDF text extraction
- Cross-document analysis, entity matching, and readiness score calculation
- Appeal draft generation, reviewer approval, and ReportLab PDF export
- Synthetic demo seeder execution

Run the tests:
```bash
# Run pytest with in-memory SQLite
$env:PYTHONPATH="backend"; .\venv\Scripts\pytest backend/tests/ -v
```

**Actual Execution Result:**
```
============================= test session starts =============================
platform win32 -- Python 3.13.11, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 5 items

backend/tests/test_all_endpoints.py::test_health_check PASSED            [ 20%]
backend/tests/test_all_endpoints.py::test_claim_lifecycle PASSED         [ 40%]
backend/tests/test_all_endpoints.py::test_document_upload_and_extraction PASSED [ 60%]
backend/tests/test_all_endpoints.py::test_end_to_end_analysis_readiness_and_appeal_export PASSED [ 80%]
backend/tests/test_all_endpoints.py::test_demo_seeder_endpoint PASSED    [100%]

============================== 5 passed in 0.58s ==============================
```

---

## 7. Exact Steps for Demonstrating to VISTERA Judges

Follow this 3-minute sequence to present ClaimForge to hackathon judges:

1. **Visit Landing Page** (`http://localhost:3000`):
   - Highlight the live metrics ticker connected directly to the backend database.
   - Explain the 4-step pipeline and the human-in-the-loop decision-support principle.
2. **Launch Demo Mode** (`/demo`):
   - View the 4 pre-packaged synthetic scenarios. Click **"Reset & Re-Seed All 4 Scenarios"** to see live database seeding.
3. **Inspect Scenario 1: Emergency Appendectomy** (`CLM-2026-9011`):
   - Show how ClaimForge detected that the insurer denied coverage for "Missing Prior Authorization" (Code `CO-197`).
   - Point to the **Appeal Readiness Score: 91/100 (High Readiness)**.
   - Show the **Rejection Analysis Finding**: ClaimForge discovered that under federal **EMTALA (42 U.S.C. § 1395dd)** and **ACA § 2719A**, prior authorization cannot be required for emergency medical conditions.
   - Click **Confirm Finding** as a human reviewer.
4. **Inspect the Cross-Document Comparison Matrix**:
   - Show how the matrix aligns dates, billed amounts, ICD-10 `K35.80`, CPT `44970`, and treating physician across the itemized bill and clinical notes.
5. **Open Appeal Letter Editor** (`/claims/[id]/appeal`):
   - Show the structured appeal draft with legal grounds, statutory citations, and exhibit references.
   - Switch Tone: Click **"Assertive Legal (ERISA/EMTALA)"** to demonstrate dynamic statutory customization.
   - Click **"Approve Draft"** to log reviewer approval.
   - Click **"Download Official PDF Packet"** to generate the styled ReportLab PDF.
6. **Create a New Claim** (`/claims/new`):
   - Fill in custom details, attach a sample document, and watch the real-time extraction and analysis pipeline run end-to-end.
