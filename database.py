"""
database.py — SQLite persistence layer for the Interview Trainer Agent.
Handles session storage and retrieval.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get("INTERVIEW_DB_PATH", "interview_sessions.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they do not exist."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate   TEXT    NOT NULL,
                job_role    TEXT    NOT NULL,
                experience  TEXT    NOT NULL,
                company     TEXT    NOT NULL,
                created_at  TEXT    NOT NULL,
                questions   TEXT    NOT NULL,   -- JSON list
                answers     TEXT    NOT NULL,   -- JSON list
                evaluations TEXT    NOT NULL,   -- JSON list of dicts
                total_score REAL    NOT NULL
            )
            """
        )
        conn.commit()


def save_session(
    candidate: str,
    job_role: str,
    experience: str,
    company: str,
    questions: list[str],
    answers: list[str],
    evaluations: list[dict],
    total_score: float,
) -> int:
    """Persist one interview session. Returns the new row id."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO sessions
                (candidate, job_role, experience, company, created_at,
                 questions, answers, evaluations, total_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate,
                job_role,
                experience,
                company,
                now,
                json.dumps(questions),
                json.dumps(answers),
                json.dumps(evaluations),
                total_score,
            ),
        )
        conn.commit()
        return cur.lastrowid


def fetch_sessions(candidate: Optional[str] = None) -> list[dict]:
    """Return all sessions, optionally filtered by candidate name (case-insensitive)."""
    with _connect() as conn:
        if candidate:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE LOWER(candidate)=LOWER(?) ORDER BY created_at DESC",
                (candidate,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sessions ORDER BY created_at DESC"
            ).fetchall()

    result = []
    for row in rows:
        d = dict(row)
        d["questions"] = json.loads(d["questions"])
        d["answers"] = json.loads(d["answers"])
        d["evaluations"] = json.loads(d["evaluations"])
        result.append(d)
    return result


def fetch_session_by_id(session_id: int) -> Optional[dict]:
    """Return a single session by primary key."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
    if row is None:
        return None
    d = dict(row)
    d["questions"] = json.loads(d["questions"])
    d["answers"] = json.loads(d["answers"])
    d["evaluations"] = json.loads(d["evaluations"])
    return d


def delete_session(session_id: int) -> None:
    """Delete a session by primary key."""
    with _connect() as conn:
        conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        conn.commit()
