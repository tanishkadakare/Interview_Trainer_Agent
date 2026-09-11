"""
ai_engine.py — Question generation and answer evaluation logic.

Uses the OpenAI Chat Completions API when an OPENAI_API_KEY env var is set.
Falls back to a rich rule-based engine so the app works without any API key.
"""

import os
import json
import re
import textwrap
from typing import Optional

# ---------------------------------------------------------------------------
# Optional OpenAI integration
# ---------------------------------------------------------------------------

try:
    from openai import OpenAI as _OpenAI  # type: ignore

    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


def _chat(prompt: str, system: str = "You are an expert technical interviewer.") -> Optional[str]:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key or not _OPENAI_AVAILABLE:
        return None
    try:
        client = _OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Fallback question bank
# ---------------------------------------------------------------------------

QUESTION_BANK: dict[str, dict[str, list[str]]] = {
    "Software Engineer": {
        "Entry": [
            "Explain the difference between a stack and a queue. When would you use each?",
            "What is object-oriented programming? Describe the four main principles.",
            "How does HTTP differ from HTTPS? Why does it matter for web applications?",
            "What is version control and why is Git important in software development?",
            "Walk me through how you would debug a program that produces unexpected output.",
        ],
        "Mid": [
            "Describe the SOLID principles and give a practical example of each.",
            "Compare relational and non-relational databases. How do you choose between them?",
            "Explain the CAP theorem and its implications for distributed systems.",
            "What design patterns have you used in production? Describe one in detail.",
            "How would you optimise a slow SQL query? Walk me through your process.",
        ],
        "Senior": [
            "How do you approach system design for a service that must handle 10 million daily active users?",
            "Describe your experience with microservices architecture. What are its trade-offs?",
            "Explain eventual consistency and how you would handle it in a distributed transaction.",
            "What strategies do you use for zero-downtime deployments?",
            "How do you build a culture of code quality and technical excellence in a team?",
        ],
    },
    "Data Scientist": {
        "Entry": [
            "What is the difference between supervised and unsupervised learning?",
            "Explain the bias-variance trade-off in machine learning models.",
            "How would you handle missing values in a dataset?",
            "What is cross-validation and why is it important?",
            "Describe the steps in a typical data science project lifecycle.",
        ],
        "Mid": [
            "Compare gradient boosting and random forests. When would you prefer one over the other?",
            "Explain how you would detect and handle class imbalance in a classification problem.",
            "What is regularisation? Explain L1 vs L2 and when you'd use each.",
            "Describe your approach to feature engineering for a tabular dataset.",
            "How do you evaluate the business impact of a machine learning model?",
        ],
        "Senior": [
            "Design an end-to-end ML pipeline for real-time fraud detection at scale.",
            "How do you approach model explainability for high-stakes decisions?",
            "Describe a situation where a model performed well offline but poorly in production. How did you diagnose it?",
            "What is concept drift, and what monitoring strategies would you put in place?",
            "How do you balance model accuracy with inference latency in production systems?",
        ],
    },
    "Product Manager": {
        "Entry": [
            "How do you prioritise features when every stakeholder believes theirs is the most important?",
            "What metrics would you track to measure the success of a newly launched feature?",
            "Describe the difference between a user story and an epic.",
            "How would you conduct user research to validate a product hypothesis?",
            "Walk me through a product you use daily and suggest one improvement.",
        ],
        "Mid": [
            "Describe your process for creating and maintaining a product roadmap.",
            "How do you handle conflicting priorities between engineering, design, and business teams?",
            "Explain how you would use A/B testing to make a product decision.",
            "Describe a time you had to kill a feature or sunset a product. How did you manage it?",
            "How do you define and communicate product vision to cross-functional teams?",
        ],
        "Senior": [
            "How would you build a product strategy for entering a new market?",
            "Describe how you would align a product organisation around a company-wide OKR.",
            "What frameworks do you use for long-term product planning and resource allocation?",
            "How do you balance short-term revenue goals with long-term platform investment?",
            "Describe a product failure you owned and the lessons you took from it.",
        ],
    },
    "DevOps Engineer": {
        "Entry": [
            "Explain the difference between continuous integration, continuous delivery, and continuous deployment.",
            "What is a container and how does Docker differ from a virtual machine?",
            "Describe the purpose of infrastructure as code (IaC). Name one tool you have used.",
            "What is a load balancer and why is it used?",
            "How would you monitor an application in production?",
        ],
        "Mid": [
            "Design a CI/CD pipeline for a microservices application deployed to Kubernetes.",
            "Explain Kubernetes concepts: Pods, Deployments, Services, and Ingress.",
            "How do you manage secrets and sensitive configuration in a cloud-native environment?",
            "Describe your approach to incident response and post-mortem analysis.",
            "Compare blue/green deployments with canary releases. When would you use each?",
        ],
        "Senior": [
            "How would you design a multi-region, highly available deployment strategy?",
            "Describe how you would reduce cloud infrastructure costs by 30% without compromising reliability.",
            "What is GitOps and how does it change the way teams manage infrastructure?",
            "How do you enforce security policies across a large Kubernetes cluster?",
            "Describe how you would build an internal developer platform to improve engineering productivity.",
        ],
    },
    "UX Designer": {
        "Entry": [
            "What is the difference between UX and UI design?",
            "Walk me through your design process from brief to final deliverable.",
            "What is a user persona and how do you create one?",
            "Explain the purpose of wireframes and prototypes in the design workflow.",
            "How do you measure whether a design is successful?",
        ],
        "Mid": [
            "Describe a design decision you made based on user research. What was the impact?",
            "How do you balance aesthetic design with accessibility requirements?",
            "Explain how you handle design critique and incorporate feedback constructively.",
            "What tools do you use for usability testing and how do you analyse the results?",
            "Describe how you collaborate with engineers to ensure design fidelity in implementation.",
        ],
        "Senior": [
            "How do you build and evolve a design system for a large product organisation?",
            "Describe your approach to establishing UX strategy and connecting it to business outcomes.",
            "How do you manage design consistency across multiple product teams?",
            "Describe a time you advocated for the user when business pressures pushed in a different direction.",
            "How do you mentor junior designers and grow UX maturity in an organisation?",
        ],
    },
}

ROLES = sorted(QUESTION_BANK.keys())
EXPERIENCE_LEVELS = ["Entry", "Mid", "Senior"]


# ---------------------------------------------------------------------------
# Public API — question generation
# ---------------------------------------------------------------------------

def generate_questions(job_role: str, experience: str, company: str) -> list[str]:
    """Return 5 interview questions for the given role / level / company."""
    # Try OpenAI first
    prompt = textwrap.dedent(f"""
        Generate exactly 5 interview questions for a {experience}-level {job_role} candidate
        applying to {company}. The questions should be specific, technical, and behavioural
        in proportion to the seniority level.

        Return ONLY a JSON array of 5 strings — no extra text, no numbering outside the JSON.
        Example format: ["Question 1?", "Question 2?", ...]
    """).strip()

    raw = _chat(prompt)
    if raw:
        try:
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                questions = json.loads(match.group())
                if isinstance(questions, list) and len(questions) >= 5:
                    return [str(q) for q in questions[:5]]
        except (json.JSONDecodeError, ValueError):
            pass

    # Fallback: bank lookup with graceful degradation
    role_bank = QUESTION_BANK.get(job_role, QUESTION_BANK["Software Engineer"])
    level_bank = role_bank.get(experience, role_bank.get("Mid", []))
    # Pad with generic questions if needed
    generic = [
        f"Why do you want to work at {company}?",
        "Describe your greatest professional achievement.",
        "How do you keep your skills current in a fast-moving industry?",
        "Tell me about a time you dealt with a difficult team member.",
        "Where do you see yourself in five years?",
    ]
    combined = level_bank + generic
    return combined[:5]


# ---------------------------------------------------------------------------
# Fallback evaluation helpers
# ---------------------------------------------------------------------------

_POSITIVE_KEYWORDS = [
    "example", "result", "because", "therefore", "implemented", "improved",
    "measured", "achieved", "learned", "specifically", "data", "metric",
    "team", "collaborated", "designed", "built", "tested", "deployed",
    "analysed", "strategy", "framework", "approach",
]

_VAGUE_PHRASES = [
    "i think", "maybe", "not sure", "i don't know", "i guess", "probably",
    "kind of", "sort of", "i believe", "something like",
]

MODEL_ANSWERS: dict[str, str] = {
    "stack": (
        "A stack is a LIFO (Last-In-First-Out) data structure used for function call management, "
        "undo operations, and expression parsing. A queue is FIFO (First-In-First-Out) and suits "
        "task scheduling, BFS traversal, and message buffering."
    ),
    "oop": (
        "OOP's four principles are Encapsulation (bundling data with methods), Inheritance "
        "(child classes reuse parent behaviour), Polymorphism (same interface, different "
        "implementations), and Abstraction (hiding implementation details)."
    ),
    "supervised": (
        "Supervised learning trains on labelled data to predict outputs (e.g. classification, "
        "regression). Unsupervised learning finds hidden patterns in unlabelled data "
        "(e.g. clustering, dimensionality reduction)."
    ),
}


def _rule_based_evaluate(question: str, answer: str) -> dict:
    """Heuristic evaluation when OpenAI is unavailable."""
    answer_lower = answer.lower().strip()
    word_count = len(answer.split())

    score = 5.0  # baseline

    # Length signal
    if word_count < 20:
        score -= 2.0
    elif word_count < 50:
        score -= 0.5
    elif word_count > 120:
        score += 0.5

    # Positive keyword density
    hits = sum(1 for kw in _POSITIVE_KEYWORDS if kw in answer_lower)
    score += min(hits * 0.3, 2.0)

    # Penalise vague language
    vague_hits = sum(1 for ph in _VAGUE_PHRASES if ph in answer_lower)
    score -= min(vague_hits * 0.5, 1.5)

    score = round(max(1.0, min(10.0, score)), 1)

    strengths = []
    improvements = []

    if word_count >= 80:
        strengths.append("Provided a detailed and thorough response.")
    if hits >= 4:
        strengths.append("Used concrete examples and specific terminology.")
    if word_count >= 50 and hits >= 2:
        strengths.append("Demonstrated relevant knowledge with structured explanation.")
    if not strengths:
        strengths.append("Attempted to address the question.")

    if word_count < 50:
        improvements.append("Expand your answer with specific examples or results.")
    if vague_hits > 0:
        improvements.append("Replace uncertain language ('I think', 'maybe') with confident, factual statements.")
    if hits < 3:
        improvements.append("Incorporate measurable outcomes, methodologies, or domain-specific terminology.")
    if not improvements:
        improvements.append("Consider structuring your answer using the STAR method for even greater clarity.")

    # Look up a model answer hint
    model_hint = next(
        (v for k, v in MODEL_ANSWERS.items() if k in question.lower()), None
    )
    model_answer = (
        model_hint
        if model_hint
        else (
            "A strong answer would include: a clear direct response to the question, "
            "at least one concrete real-world example, measurable outcomes or data where "
            "applicable, and a reflection on what you learned or would do differently."
        )
    )

    return {
        "score": score,
        "strengths": strengths,
        "improvements": improvements,
        "model_answer": model_answer,
    }


# ---------------------------------------------------------------------------
# Public API — evaluation
# ---------------------------------------------------------------------------

def evaluate_answer(question: str, answer: str, job_role: str, experience: str) -> dict:
    """
    Evaluate a single answer. Returns:
        {score: float, strengths: list[str], improvements: list[str], model_answer: str}
    """
    if not answer.strip():
        return {
            "score": 0.0,
            "strengths": [],
            "improvements": ["No answer was provided."],
            "model_answer": "Please attempt to answer the question.",
        }

    prompt = textwrap.dedent(f"""
        You are evaluating a {experience}-level {job_role} candidate.

        Interview question:
        "{question}"

        Candidate's answer:
        "{answer}"

        Evaluate the answer and return a JSON object with exactly these keys:
        - "score": a number from 0 to 10 (one decimal place)
        - "strengths": a list of 1-3 specific strengths (strings)
        - "improvements": a list of 1-3 specific, actionable improvement suggestions (strings)
        - "model_answer": a concise model answer (2-4 sentences) the candidate should aspire to

        Return ONLY valid JSON, no extra text.
    """).strip()

    raw = _chat(prompt)
    if raw:
        try:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                result = json.loads(match.group())
                # Validate shape
                if all(k in result for k in ("score", "strengths", "improvements", "model_answer")):
                    result["score"] = round(float(result["score"]), 1)
                    return result
        except (json.JSONDecodeError, ValueError, TypeError):
            pass

    return _rule_based_evaluate(question, answer)


def evaluate_all(
    questions: list[str], answers: list[str], job_role: str, experience: str
) -> tuple[list[dict], float]:
    """
    Evaluate all question/answer pairs.
    Returns (evaluations_list, average_score).
    """
    evaluations = []
    for q, a in zip(questions, answers):
        evaluations.append(evaluate_answer(q, a, job_role, experience))
    total = sum(e["score"] for e in evaluations)
    avg = round(total / len(evaluations), 1) if evaluations else 0.0
    return evaluations, avg
