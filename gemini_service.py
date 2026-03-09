import json
import os
from typing import Dict, List

import google.generativeai as genai


class GeminiServiceError(Exception):
    """Raised when the Gemini-backed generation pipeline fails."""


def _model() -> genai.GenerativeModel:
    """Create Gemini model client from environment configuration."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise GeminiServiceError(
            "GEMINI_API_KEY is not set. Please configure it in your environment."
        )

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return genai.GenerativeModel(model_name)


def _extract_json_object(raw_text: str) -> Dict:
    """Parse raw model output into JSON, handling fenced payloads."""
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:].strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or start >= end:
        raise GeminiServiceError("Gemini response did not contain a valid JSON object.")

    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise GeminiServiceError("Could not parse Gemini response as JSON.") from exc


def extract_key_paragraphs_gemini(article_text: str) -> List[str]:
    """Use Gemini to select the 4 most important paragraphs from article text."""
    prompt = f"""
You are an expert reading-comprehension assistant.
From the article text below, identify the 4 most important paragraphs that best capture:
1) the central thesis,
2) key supporting arguments,
3) nuanced reasoning,
4) conclusion/implications.

Return strictly valid JSON in this shape:
{{
  "paragraphs": ["paragraph1", "paragraph2", "paragraph3", "paragraph4"]
}}

Article text:
{article_text}
""".strip()

    try:
        response = _model().generate_content(
            prompt,
            generation_config={"temperature": 0.2},
        )
        payload = _extract_json_object(getattr(response, "text", ""))
        paragraphs = payload.get("paragraphs", [])
        if not isinstance(paragraphs, list) or len(paragraphs) != 4:
            raise GeminiServiceError("Gemini did not return exactly 4 paragraphs.")
        return [str(p).strip() for p in paragraphs]
    except Exception as exc:
        if isinstance(exc, GeminiServiceError):
            raise
        raise GeminiServiceError(f"Gemini paragraph extraction failed: {exc}") from exc


def generate_cat_questions_gemini(paragraphs: List[str]) -> List[Dict]:
    """Use Gemini to generate 5 CAT-style MCQs from selected paragraphs."""
    prompt = f"""
You are an IIM CAT verbal ability and reading comprehension question setter.
Using only the paragraphs below, generate exactly 5 CAT-style multiple-choice questions.
Distribute question types across:
- Reading comprehension
- Logical inference
- Vocabulary in context
- Critical reasoning
- Main idea identification

Return strictly valid JSON in this format:
{{
  "questions": [
    {{
      "question": "...",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "correct_answer": "A",
      "incorrect_explanation": "Why common wrong choices are wrong.",
      "correct_explanation": "Why the correct choice is best."
    }}
  ]
}}

Paragraphs:
{json.dumps(paragraphs, ensure_ascii=False, indent=2)}
""".strip()

    try:
        response = _model().generate_content(
            prompt,
            generation_config={"temperature": 0.4},
        )
        payload = _extract_json_object(getattr(response, "text", ""))
        questions = payload.get("questions", [])

        if not isinstance(questions, list) or len(questions) != 5:
            raise GeminiServiceError("Gemini did not return exactly 5 questions.")

        for question in questions:
            if not all(key in question for key in ["question", "options", "correct_answer"]):
                raise GeminiServiceError("Question payload is missing required keys.")
            options = question.get("options", {})
            if sorted(options.keys()) != ["A", "B", "C", "D"]:
                raise GeminiServiceError("Each question must contain options A, B, C, and D.")

        return questions
    except Exception as exc:
        if isinstance(exc, GeminiServiceError):
            raise
        raise GeminiServiceError(f"Gemini question generation failed: {exc}") from exc
