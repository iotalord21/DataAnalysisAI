# 📊 Autonomous Data Analysis Agent

An end-to-end, production-oriented **Autonomous Data Analysis Agent** system built with **FastAPI**, **LangGraph**, **React**, and **Plotly**.

The platform ingests raw tabular datasets (CSV / Excel) alongside natural language questions, autonomously decomposes objectives into quantitative hypotheses, generates and audits sandboxed Python/SQL code, synthesizes interactive Plotly charts, produces qualitative insights backed by concrete evidence, and strictly verifies all findings against ground-truth outputs before delivering an executive dashboard.

---

## 🔄 Core Agentic Workflow & Architecture

The architecture implements a rigorous cyclic state machine:  
**`Plan → Act → Observe → Verify → Re-plan → Report`**

```
User uploads CSV/Excel & asks question
        ↓
Data Profiler Agent (Clean, Schema, Null & Outlier Detection)
        ↓
Planner Agent (Goal Decomposition & Analytical Hypotheses)
        ↓
┌─────────────────────────────────────────────────────────────┐
│ Analysis Agent (Python REPL / DuckDB SQL Execution Sandbox) │
│ • Summary Statistics & Distributions                        │
│ • Correlation & Bivariate Analysis                          │
│ • Trend Analysis & Cohort Comparisons                       │
│ • Outlier & Leverage Point Identification                   │
│ • Category Segmentation                                     │
└──────────────────────────────┬──────────────────────────────┘
                               ↓
Visualization Agent (Generates Interactive Plotly JSON Specs)
                               ↓
Insight Agent (Extracts Patterns & Evidence-Backed Findings)
                               ↓
Verification Agent (Math & Consistency Audit)
          ↙                         ↘
       Valid                      Invalid / Discrepancy
         ↓                          ↓
    Report Agent                Re-plan Node (Incorporates audit feedback)
         ↓                          ↓
Interactive React Dashboard     Analysis Agent (Self-correcting re-analysis)
+ Downloadable Report
```

---

## 🛡️ Sandbox & Isolation Layer

To protect system integrity while granting the LLM analytical autonomy, all generated code is executed within an isolated environment:
- **AST Security Filter (`security.py`)**: Inspects Abstract Syntax Trees to reject dangerous imports (`os`, `sys`, `subprocess`, `socket`, `requests`, `builtins`) and forbidden reflection/eval calls before code execution.
- **Process Isolation (`runner_script.py`)**: Executes in a standalone subprocess with pre-warmed Pandas and DuckDB contexts.
- **Strict Execution Timeouts**: Hard execution deadline (e.g. 20s) prevents runaway calculations or infinite loops.
- **Read-Only DuckDB Engine (`sql_runner.py`)**: Prohibits data-mutating SQL keywords (`DROP`, `DELETE`, `INSERT`, `ALTER`), enabling lightning-fast analytical queries over large CSV files.

---

## 🤖 Specialized Multi-Agent Roles

| Agent | Responsibility | Core Tools |
| :--- | :--- | :--- |
| **Data Agent** | Schema inference, null checks, cardinality, descriptive stats, prompt optimization | `DataProfiler`, `pandas` |
| **Planner Agent** | Strategic goal decomposition, testable quantitative hypotheses | LLM, structured JSON |
| **Analysis Agent** | Generates executable code, runs sandbox computations, self-corrects runtime errors | `PythonReplTool`, `DuckDB` |
| **Visualization Agent** | Selects optimal chart paradigms, crafts responsive Plotly specifications | `Plotly.js`, `px`, `go` |
| **Insight Agent** | Domain synthesis, extracts qualitative findings tied to verified numbers | LLM, pattern heuristics |
| **Verification Agent** | Audits numerical claims, verifies chart trace integrity, computes confidence score | Regex auditor, consistency validator |
| **Report Agent** | Synthesizes executive summary, KPI badges, and downloadable HTML/Markdown reports | `Jinja2`, Markdown renderer |

---

## 📁 Repository Structure

```
DataAnalysisAI/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry point, CORS & healthcheck
│   │   ├── config.py                   # Pydantic settings & paths
│   │   ├── api/
│   │   │   ├── datasets.py             # File uploads, samples, tabular preview
│   │   │   └── analysis.py             # Sync execution, SSE stream, report export
│   │   ├── agents/
│   │   │   ├── state.py                # LangGraph State & Pydantic models
│   │   │   ├── graph.py                # StateGraph assembly & conditional loops
│   │   │   ├── llm_factory.py          # Provider-agnostic factory (Gemini, OpenAI, Anthropic, Ollama)
│   │   │   ├── data_agent.py           # Profiling & data prep
│   │   │   ├── planner_agent.py        # Analysis planning & hypothesis formulation
│   │   │   ├── analysis_agent.py       # Code generation & sandboxed execution
│   │   │   ├── visualization_agent.py  # Plotly chart generation
│   │   │   ├── insight_agent.py        # Strategic pattern synthesis
│   │   │   ├── verification_agent.py   # Consistency & math verification
│   │   │   └── report_agent.py         # Executive report generator
│   │   ├── tools/
│   │   │   ├── security.py             # AST-based code isolation validator
│   │   │   ├── python_repl.py          # Subprocess runner with timeout
│   │   │   ├── runner_script.py        # Worker process execution harness
│   │   │   ├── sql_runner.py           # Read-only DuckDB SQL engine
│   │   │   └── data_profiler.py        # Automated stats & prompt formatter
│   │   └── storage/
│   │       ├── sample_data/            # Bundled SaaS Churn dataset
│   │       ├── uploads/                # Active dataset sessions
│   │       └── reports/                # Exported reports
│   ├── tests/
│   │   └── test_tools.py               # Unit tests for security sandbox & tools
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Navbar.tsx              # Brand header with status badges
│   │   │   ├── DatasetUpload.tsx       # Drag-and-drop file upload & sample loader
│   │   │   ├── AgentTimeline.tsx       # Real-time visual agentic stage stepper
│   │   │   ├── Dashboard.tsx           # Primary results container
│   │   │   ├── PlotlyChart.tsx         # Interactive Plotly chart with dark theme & zoom
│   │   │   ├── InsightsFeed.tsx        # Verified insight cards with quantitative evidence
│   │   │   ├── CodeViewer.tsx          # Reproducible executed Python script viewer
│   │   │   └── ReportModal.tsx         # Full executive report with HTML/MD export
│   │   ├── services/
│   │   │   └── api.ts                  # Axios client & Server-Sent Events listener
│   │   ├── types/
│   │   │   └── index.ts                # TypeScript interfaces
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── .env.example
└── README.md
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- **Google Gemini API Key** (or OpenAI / Anthropic key)

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Add your API key:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

*(You can also set `LLM_PROVIDER=openai` or `LLM_PROVIDER=anthropic` if desired).*

### 3. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate

# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

Run test suite:
```bash
python -m pytest tests/test_tools.py -v
```

Launch FastAPI server:
```bash
python run.py
```
*Backend runs on `http://localhost:8000` (API Docs at `http://localhost:8000/docs`).*

### 4. Frontend Setup
In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on `http://localhost:5173`.*

---

## 📈 Verification Audit & Trust
Unlike standard chatbot analysts that may hallucinate statistics, this platform features an explicit **Verification Agent**:
1. It parses every qualitative claim and extracts numerical tokens.
2. It audits these numbers directly against the stdout and dataframe results recorded by the isolated Python runner.
3. If discrepancies or execution errors are detected, the orchestrator triggers an automatic **Re-analysis cycle** (`max_retries = 2`) with corrective guidance.
4. Only verified conclusions receive the audit badge in the final dashboard.
