"""
Module 4 — optional AI enhancement layer.

Per the tech spec (Novapath), AI = Google Gemini API. This is deliberately
a thin, optional layer on TOP of planner.py's deterministic algorithm —
not a replacement for it. The algorithm decides the schedule (what fits
when); Gemini only helps enrich task descriptions with better,
personalized explanations.

If no API key is configured, every function here is a safe no-op and
the app runs fine on the plain algorithm alone. This matters for
demoing/dev without burning API quota, and means a missing/invalid key
never breaks plan generation.
"""

import os
import json
from typing import List
from app.services.planner import PlannedDay

AI_ENABLED = bool(os.getenv("GEMINI_API_KEY"))

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def enhance_day_with_ai(day: PlannedDay, skill_level: str, learning_goal: str) -> PlannedDay:
    """
    If GEMINI_API_KEY is configured, ask Gemini to rewrite task
    descriptions to be more specific/useful given the user's skill level
    and goal. If anything goes wrong (no key, network error, bad
    response), we silently fall back to the original algorithm-generated
    descriptions so the app never breaks because of the AI layer.
    """
    if not AI_ENABLED:
        return day

    try:
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(GEMINI_MODEL)

        topic_list = ", ".join(sorted({t.topic_title for t in day.tasks}))
        prompt = (
            f"A student at '{skill_level}' level, whose goal is "
            f"'{learning_goal}', is studying: {topic_list} today. "
            f"Here are their planned tasks:\n"
            + "\n".join(f"- {t.task_title} ({t.estimated_minutes} min)" for t in day.tasks)
            + "\n\nRewrite each task's description in one short, specific, "
            "encouraging sentence tailored to their skill level. "
            "Return ONLY a JSON array of strings, one per task, in the "
            "same order as listed above. No preamble, no markdown."
        )

        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )

        descriptions = json.loads(response.text.strip().strip("`"))

        if isinstance(descriptions, list) and len(descriptions) == len(day.tasks):
            for task, new_description in zip(day.tasks, descriptions):
                task.description = new_description

    except Exception:
        # AI enrichment is a nice-to-have, never a hard dependency.
        # In production you'd log this; for now we just fall back silently.
        pass

    return day


def enhance_plan_with_ai(
    days: List[PlannedDay], skill_level: str, learning_goal: str
) -> List[PlannedDay]:
    """Apply Gemini enhancement to every day in the plan, if enabled."""
    if not AI_ENABLED:
        return days
    return [enhance_day_with_ai(d, skill_level, learning_goal) for d in days]


def generate_quiz_questions(topic_title: str, skill_level: str, count: int = 3) -> list:
    """
    Bonus helper for whoever builds Module 8 (Adaptive Quiz System) —
    not wired into any route yet, but ready to use since Gemini is
    already configured here. Returns [] if AI isn't enabled or on any
    error, same fail-safe pattern as the rest of this file.

    Returns a list of dicts: {"question": str, "options": [str, ...],
    "correct_index": int, "explanation": str}
    """
    if not AI_ENABLED:
        return []

    try:
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel(GEMINI_MODEL)

        prompt = (
            f"Generate {count} multiple-choice quiz questions about "
            f"'{topic_title}' for a {skill_level}-level learner. "
            'Return ONLY a JSON array of objects shaped like: '
            '{"question": "...", "options": ["...", "...", "...", "..."], '
            '"correct_index": 0, "explanation": "..."}. No preamble, no markdown.'
        )

        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        questions = json.loads(response.text.strip().strip("`"))
        return questions if isinstance(questions, list) else []

    except Exception:
        return []
