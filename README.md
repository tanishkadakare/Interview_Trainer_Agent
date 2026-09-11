# 🎯 Interview Trainer Agent

A fully functional, AI-powered mock interview web application built with **Python** and **Streamlit**.  
It generates role-specific interview questions, evaluates your answers with detailed feedback, and tracks your progress over multiple sessions.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Role-Specific Questions** | 5 tailored questions generated for your chosen job role, experience level, and target company |
| **AI Evaluation** | Each answer is scored /10 with identified strengths, actionable improvements, and a model answer |
| **OpenAI Integration** | Plug in your own `OPENAI_API_KEY` for GPT-4o-mini powered generation & evaluation |
| **Built-in Engine** | A rich rule-based fallback works with zero API key or internet connection |
| **Session History** | All completed sessions are saved to a local SQLite database |
| **Progress Chart** | Line chart shows your score progression across multiple attempts |
| **Clean Dashboard** | Responsive two-tab Streamlit UI with sidebar candidate profile |

---

## 🗂 Project Structure

```
Interview_Trainer_Agent/
├── app.py                   # Main Streamlit application
├── ai_engine.py             # Question generation + answer evaluation logic
├── database.py              # SQLite persistence layer
├── requirements.txt         # Python dependencies
├── README.md                # This file
└── interview_sessions.db    # Auto-created on first run (SQLite database)
```

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.11+** (3.10 minimum)
- `pip` package manager

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
streamlit run app.py
```

The app will open automatically at **http://localhost:8501**.

---

## 🔑 OpenAI API Key (Optional)

The app works completely offline with its built-in evaluation engine.  
To unlock GPT-4o-mini powered question generation and answer evaluation:

**Option A — Enter in the app sidebar**  
Paste your key into the *OpenAI API Key* field in the sidebar. It is used only for the current session and never stored.

**Option B — Environment variable**

```bash
# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."

# macOS / Linux
export OPENAI_API_KEY="sk-..."

streamlit run app.py
```

**Option C — `.env` file** (requires `python-dotenv`):

```
OPENAI_API_KEY=sk-...
```

---

## 🖥 How to Use

1. **Fill in your profile** in the left sidebar:
   - Full Name
   - Job Role (Software Engineer, Data Scientist, Product Manager, DevOps Engineer, UX Designer)
   - Experience Level (Entry / Mid / Senior)
   - Target Company

2. **Click "Generate Questions"** — 5 tailored interview questions are created.

3. **Answer all questions** in the text areas provided.

4. **Click "Submit & Evaluate"** — each answer is scored and detailed feedback is shown.

5. **Save the session** with the "Save Session" button to persist it to the local database.

6. **Track progress** in the **History & Progress** tab — view past sessions and your score trend.

---

## 🗄 Database

Sessions are stored in `interview_sessions.db` (SQLite, auto-created in the working directory).

### Schema

```sql
CREATE TABLE sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate   TEXT    NOT NULL,
    job_role    TEXT    NOT NULL,
    experience  TEXT    NOT NULL,
    company     TEXT    NOT NULL,
    created_at  TEXT    NOT NULL,
    questions   TEXT    NOT NULL,   -- JSON array
    answers     TEXT    NOT NULL,   -- JSON array
    evaluations TEXT    NOT NULL,   -- JSON array of objects
    total_score REAL    NOT NULL
);
```

To use a custom database path:

```bash
$env:INTERVIEW_DB_PATH = "C:\MyData\interviews.db"
streamlit run app.py
```

---

## 🧩 Supported Roles & Levels

| Role | Entry | Mid | Senior |
|---|---|---|---|
| Software Engineer | ✅ | ✅ | ✅ |
| Data Scientist | ✅ | ✅ | ✅ |
| Product Manager | ✅ | ✅ | ✅ |
| DevOps Engineer | ✅ | ✅ | ✅ |
| UX Designer | ✅ | ✅ | ✅ |

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `streamlit` | ≥ 1.35.0 | Web UI framework |
| `pandas` | ≥ 2.0.0 | History table & chart data |
| `openai` | ≥ 1.0.0 | Optional GPT-4o-mini integration |

All other libraries (`sqlite3`, `json`, `re`, `os`) are part of the Python standard library.

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: streamlit` | Run `pip install -r requirements.txt` |
| App does not open automatically | Navigate to `http://localhost:8501` manually |
| Port 8501 already in use | Run `streamlit run app.py --server.port 8502` |
| OpenAI errors / rate limits | The app falls back to the built-in engine automatically |
| Database locked error | Ensure only one instance of the app is running |

---

## 📄 License

MIT License — free to use, modify, and distribute.
