"""
app.py — Interview Trainer Agent
A Streamlit web application that generates role-specific interview questions,
evaluates candidate answers, and persists session history to SQLite.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

import database as db
import ai_engine as ai

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Interview Trainer Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    /* ── Sidebar shell ─────────────────────────────────────────────────── */
    [data-testid="stSidebar"] { background: #0f172a; }

    /* Sidebar prose text (headings, markdown, captions) */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span:not([data-baseweb]),
    [data-testid="stSidebar"] .stMarkdown { color: #e2e8f0 !important; }

    /* Sidebar widget labels */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stTextInput label { color: #94a3b8 !important; font-size: 0.8rem; }

    /* ── Sidebar input fields — crisp white background, black text ─────── */
    [data-testid="stSidebar"] [data-baseweb="input"],
    [data-testid="stSidebar"] [data-baseweb="select"] {
        background-color: #ffffff !important;
        border-color: #334155 !important;
        border-radius: 6px !important;
    }
    /* Typed text inside text inputs */
    [data-testid="stSidebar"] [data-baseweb="input"] input {
        color: #0f172a !important;
        background-color: #ffffff !important;
        caret-color: #0f172a !important;
    }
    /* Selected value text inside selectboxes */
    [data-testid="stSidebar"] [data-baseweb="select"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="select"] div[class*="ValueContainer"] {
        color: #0f172a !important;
    }
    /* Placeholder text */
    [data-testid="stSidebar"] [data-baseweb="input"] input::placeholder { color: #94a3b8 !important; }
    /* Password eye-icon and clear button */
    [data-testid="stSidebar"] [data-baseweb="input"] button svg { fill: #475569 !important; }

    /* Cards */
    .card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1.4rem 1.6rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .card-title { font-weight: 700; font-size: 1rem; color: #0f172a; margin-bottom: 0.6rem; }

    /* Score badge */
    .score-badge {
        display: inline-block;
        padding: 0.3rem 0.9rem;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 1.1rem;
        color: #fff;
    }
    .score-high   { background: #16a34a; }
    .score-mid    { background: #ca8a04; }
    .score-low    { background: #dc2626; }

    /* Question number chip */
    .q-chip {
        background: #3b82f6;
        color: #fff !important;
        border-radius: 50%;
        width: 28px; height: 28px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }

    /* Feedback sections */
    .feedback-strength { color: #15803d; font-size: 0.9rem; }
    .feedback-improve  { color: #b45309; font-size: 0.9rem; }
    .feedback-model    { color: #1e40af; font-size: 0.9rem; background: #eff6ff;
                         border-left: 3px solid #3b82f6; padding: 0.5rem 0.8rem;
                         border-radius: 0 6px 6px 0; margin-top: 0.5rem; }

    /* History table */
    .st-emotion-cache-1v0mbdj { border-radius: 8px; }

    /* Section headers */
    .section-header {
        font-size: 1.25rem; font-weight: 700; color: #0f172a;
        border-bottom: 2px solid #3b82f6;
        padding-bottom: 0.35rem; margin-bottom: 1.2rem;
    }

    /* Progress bar override */
    .stProgress > div > div { background: #3b82f6; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# DB initialisation (runs once at startup)
# ---------------------------------------------------------------------------

db.init_db()

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

defaults = {
    "questions": [],
    "answers": [""] * 5,
    "evaluations": [],
    "total_score": 0.0,
    "stage": "setup",          # setup | answering | results
    "session_saved": False,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ---------------------------------------------------------------------------
# Sidebar — candidate profile
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 🎯 Interview Trainer")
    st.markdown("---")
    st.markdown("### Candidate Profile")

    candidate_name = st.text_input("Full Name", placeholder="e.g. Alex Johnson")
    job_role = st.selectbox("Job Role", ai.ROLES)
    experience = st.selectbox("Experience Level", ai.EXPERIENCE_LEVELS)
    target_company = st.text_input("Target Company", placeholder="e.g. Google")

    st.markdown("---")
    api_key_input = st.text_input(
        "OpenAI API Key (optional)",
        type="password",
        help="Provide your key for AI-powered questions & evaluation. Leave blank to use the built-in engine.",
    )
    if api_key_input:
        import os
        os.environ["OPENAI_API_KEY"] = api_key_input

    st.markdown("---")
    st.markdown(
        "<small style='color:#64748b'>Built for Problem Statement #22<br>Interview Trainer Agent</small>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Helper — score badge HTML
# ---------------------------------------------------------------------------

def score_badge(score: float) -> str:
    cls = "score-high" if score >= 7 else ("score-mid" if score >= 4 else "score-low")
    return f'<span class="score-badge {cls}">{score}/10</span>'


# ---------------------------------------------------------------------------
# Main area — tab layout
# ---------------------------------------------------------------------------

tab_interview, tab_history = st.tabs(["📝 Interview Session", "📊 History & Progress"])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — Interview Session
# ═══════════════════════════════════════════════════════════════════════════

with tab_interview:

    # Header
    st.markdown('<div class="section-header">Interview Session</div>', unsafe_allow_html=True)

    # ── STAGE: setup ────────────────────────────────────────────────────────
    if st.session_state.stage == "setup":
        col_info, col_start = st.columns([3, 1])
        with col_info:
            st.markdown(
                f"""
                <div class="card">
                    <div class="card-title">Ready to start your mock interview?</div>
                    Fill in your profile in the sidebar, then click <b>Generate Questions</b>.
                    You will receive 5 tailored interview questions. Answer each one, then
                    submit for AI-powered feedback and a score out of 10.<br><br>
                    <b>Current profile:</b><br>
                    👤 <b>Name:</b> {candidate_name or '—'} &nbsp;|&nbsp;
                    💼 <b>Role:</b> {job_role} &nbsp;|&nbsp;
                    📈 <b>Level:</b> {experience} &nbsp;|&nbsp;
                    🏢 <b>Company:</b> {target_company or '—'}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_start:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 Generate Questions", use_container_width=True, type="primary"):
                if not candidate_name.strip():
                    st.error("Please enter your name in the sidebar.")
                elif not target_company.strip():
                    st.error("Please enter your target company in the sidebar.")
                else:
                    with st.spinner("Generating questions…"):
                        qs = ai.generate_questions(job_role, experience, target_company)
                    st.session_state.questions = qs
                    st.session_state.answers = [""] * len(qs)
                    st.session_state.evaluations = []
                    st.session_state.total_score = 0.0
                    st.session_state.session_saved = False
                    st.session_state.stage = "answering"
                    st.rerun()

    # ── STAGE: answering ────────────────────────────────────────────────────
    elif st.session_state.stage == "answering":
        questions = st.session_state.questions

        st.markdown(
            f"""
            <div class="card">
                <div class="card-title">
                    Mock Interview — {job_role} ({experience} level) @ {target_company}
                </div>
                Answer all 5 questions below, then click <b>Submit & Evaluate</b>.
                Take your time — treat this as a real interview.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("answers_form"):
            answers_draft = []
            for idx, question in enumerate(questions):
                st.markdown(
                    f'<span class="q-chip">{idx + 1}</span><b>{question}</b>',
                    unsafe_allow_html=True,
                )
                ans = st.text_area(
                    label=f"answer_{idx}",
                    label_visibility="collapsed",
                    placeholder="Type your answer here…",
                    height=130,
                    key=f"ans_{idx}",
                )
                answers_draft.append(ans)
                st.markdown("")

            col_sub, col_reset = st.columns([2, 1])
            with col_sub:
                submitted = st.form_submit_button(
                    "✅ Submit & Evaluate", use_container_width=True, type="primary"
                )
            with col_reset:
                reset = st.form_submit_button(
                    "🔄 Start Over", use_container_width=True
                )

        if submitted:
            filled = [a.strip() for a in answers_draft]
            blanks = sum(1 for a in filled if not a)
            if blanks == len(filled):
                st.error("Please answer at least one question before submitting.")
            else:
                with st.spinner("Evaluating your answers…"):
                    evals, avg = ai.evaluate_all(questions, filled, job_role, experience)
                st.session_state.answers = filled
                st.session_state.evaluations = evals
                st.session_state.total_score = avg
                st.session_state.stage = "results"
                st.rerun()

        if reset:
            for key in ("questions", "evaluations", "session_saved"):
                del st.session_state[key]
            st.session_state.answers = [""] * 5
            st.session_state.total_score = 0.0
            st.session_state.stage = "setup"
            st.rerun()

    # ── STAGE: results ───────────────────────────────────────────────────────
    elif st.session_state.stage == "results":
        questions = st.session_state.questions
        answers = st.session_state.answers
        evaluations = st.session_state.evaluations
        total_score = st.session_state.total_score

        # ── Overall summary ──────────────────────────────────────────────
        st.markdown('<div class="section-header">Results Summary</div>', unsafe_allow_html=True)

        col_score, col_bar, col_actions = st.columns([1, 2, 1])

        with col_score:
            badge_cls = "score-high" if total_score >= 7 else ("score-mid" if total_score >= 4 else "score-low")
            st.markdown(
                f"""
                <div class="card" style="text-align:center">
                    <div style="font-size:0.85rem;color:#64748b;margin-bottom:0.3rem">OVERALL SCORE</div>
                    <span class="score-badge {badge_cls}" style="font-size:2rem;padding:0.6rem 1.5rem">
                        {total_score}/10
                    </span>
                    <div style="margin-top:0.6rem;font-size:0.85rem;color:#64748b">
                        {candidate_name or "Candidate"}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_bar:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            for i, ev in enumerate(evaluations):
                st.markdown(
                    f"<small><b>Q{i+1}</b></small>",
                    unsafe_allow_html=True,
                )
                st.progress(ev["score"] / 10, text=f"{ev['score']}/10")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_actions:
            st.markdown("<br>", unsafe_allow_html=True)
            if not st.session_state.session_saved:
                if st.button("💾 Save Session", use_container_width=True, type="primary"):
                    db.save_session(
                        candidate=candidate_name or "Anonymous",
                        job_role=job_role,
                        experience=experience,
                        company=target_company or "Unknown",
                        questions=questions,
                        answers=answers,
                        evaluations=evaluations,
                        total_score=total_score,
                    )
                    st.session_state.session_saved = True
                    st.success("Session saved!")
            else:
                st.success("✅ Saved")

            if st.button("🔄 New Interview", use_container_width=True):
                st.session_state.stage = "setup"
                st.session_state.questions = []
                st.session_state.answers = [""] * 5
                st.session_state.evaluations = []
                st.session_state.total_score = 0.0
                st.session_state.session_saved = False
                st.rerun()

        # ── Per-question feedback ────────────────────────────────────────
        st.markdown(
            '<div class="section-header" style="margin-top:1.5rem">Detailed Feedback</div>',
            unsafe_allow_html=True,
        )

        for idx, (question, answer, ev) in enumerate(
            zip(questions, answers, evaluations)
        ):
            with st.expander(
                f"Q{idx+1}: {question[:80]}{'…' if len(question) > 80 else ''}  —  Score: {ev['score']}/10",
                expanded=(idx == 0),
            ):
                c_left, c_right = st.columns([1, 1])
                with c_left:
                    st.markdown("**Question**")
                    st.info(question)
                    st.markdown("**Your Answer**")
                    st.markdown(
                        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;"
                        f"padding:0.8rem;font-size:0.9rem'>{answer or '<i>No answer provided</i>'}</div>",
                        unsafe_allow_html=True,
                    )

                with c_right:
                    st.markdown(
                        f"**Score** &nbsp; {score_badge(ev['score'])}",
                        unsafe_allow_html=True,
                    )
                    st.markdown("**Strengths ✅**")
                    for s in ev.get("strengths", []):
                        st.markdown(
                            f'<div class="feedback-strength">✔ {s}</div>',
                            unsafe_allow_html=True,
                        )
                    st.markdown("**Areas for Improvement 🔧**")
                    for imp in ev.get("improvements", []):
                        st.markdown(
                            f'<div class="feedback-improve">▲ {imp}</div>',
                            unsafe_allow_html=True,
                        )
                    st.markdown("**Model Answer 💡**")
                    st.markdown(
                        f'<div class="feedback-model">{ev.get("model_answer", "")}</div>',
                        unsafe_allow_html=True,
                    )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — History & Progress
# ═══════════════════════════════════════════════════════════════════════════

with tab_history:
    st.markdown('<div class="section-header">Session History</div>', unsafe_allow_html=True)

    col_filter, col_refresh = st.columns([3, 1])
    with col_filter:
        filter_name = st.text_input(
            "Filter by candidate name", placeholder="Leave blank to show all sessions"
        )
    with col_refresh:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    sessions = db.fetch_sessions(candidate=filter_name.strip() if filter_name.strip() else None)

    if not sessions:
        st.info("No sessions recorded yet. Complete an interview and save it to see your history here.")
    else:
        # Summary table
        table_data = []
        for s in sessions:
            badge_cls = "score-high" if s["total_score"] >= 7 else ("score-mid" if s["total_score"] >= 4 else "score-low")
            table_data.append(
                {
                    "ID": s["id"],
                    "Date": s["created_at"],
                    "Candidate": s["candidate"],
                    "Role": s["job_role"],
                    "Level": s["experience"],
                    "Company": s["company"],
                    "Score": f"{s['total_score']}/10",
                }
            )
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Progress chart (per-candidate if filtered)
        if len(sessions) > 1:
            st.markdown("### Score Progression")
            chart_data = pd.DataFrame(
                {
                    "Session": [f"#{s['id']} ({s['created_at'][:10]})" for s in reversed(sessions)],
                    "Score": [s["total_score"] for s in reversed(sessions)],
                }
            ).set_index("Session")
            st.line_chart(chart_data, y="Score", use_container_width=True)

        # Detail expander for each session
        st.markdown("### Session Details")
        for s in sessions:
            label = (
                f"[#{s['id']}] {s['created_at'][:16]}  |  "
                f"{s['candidate']} — {s['job_role']} ({s['experience']}) @ {s['company']}  |  "
                f"Score: {s['total_score']}/10"
            )
            with st.expander(label):
                for i, (q, a, ev) in enumerate(
                    zip(s["questions"], s["answers"], s["evaluations"])
                ):
                    st.markdown(f"**Q{i+1}: {q}**")
                    st.markdown(
                        f"<div style='background:#f8fafc;border:1px solid #e2e8f0;"
                        f"border-radius:6px;padding:0.6rem;font-size:0.85rem;margin-bottom:0.5rem'>"
                        f"{a or '<i>No answer</i>'}</div>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"Score: {score_badge(ev['score'])} &nbsp; "
                        f"<span class='feedback-strength'>"
                        f"{'  |  '.join(ev.get('strengths', []))}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown("---")

                col_del, _ = st.columns([1, 3])
                with col_del:
                    if st.button(f"🗑 Delete Session #{s['id']}", key=f"del_{s['id']}"):
                        db.delete_session(s["id"])
                        st.success(f"Session #{s['id']} deleted.")
                        st.rerun()
