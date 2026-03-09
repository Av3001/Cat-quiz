import json
import os
from typing import List, Dict

from openai import OpenAI


class OpenAIServiceError(Exception):
    """Raised when the OpenAI-backed generation pipeline fails."""


def _client() -> OpenAI:
    """Create a client using OPENAI_API_KEY from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise OpenAIServiceError(
            "OPENAI_API_KEY is not set. Please configure it in your environment."
        )
    return OpenAI(api_key=api_key)


def extract_key_paragraphs(article_text: str) -> List[str]:
    """Ask the model to select the 4 most important paragraphs as JSON array."""
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
        response = _client().chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        paragraphs = payload.get("paragraphs", [])

        if not isinstance(paragraphs, list) or len(paragraphs) != 4:
            raise OpenAIServiceError("Model did not return exactly 4 paragraphs.")

        return [str(p).strip() for p in paragraphs]
    except json.JSONDecodeError as exc:
        raise OpenAIServiceError(
            "Could not parse paragraph extraction response as JSON."
        ) from exc
    except Exception as exc:
        if isinstance(exc, OpenAIServiceError):
            raise
        raise OpenAIServiceError(f"Paragraph extraction failed: {exc}") from exc


def generate_cat_questions(paragraphs: List[str]) -> List[Dict]:
    """Generate 5 CAT-style MCQs from the selected paragraphs."""
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
        response = _client().chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        questions = payload.get("questions", [])

        if not isinstance(questions, list) or len(questions) != 5:
            raise OpenAIServiceError("Model did not return exactly 5 questions.")

        for question in questions:
            if not all(key in question for key in ["question", "options", "correct_answer"]):
                raise OpenAIServiceError("Question payload is missing required keys.")
            options = question.get("options", {})
            if sorted(options.keys()) != ["A", "B", "C", "D"]:
                raise OpenAIServiceError("Each question must contain options A, B, C, and D.")

        return questions
    except json.JSONDecodeError as exc:
        raise OpenAIServiceError(
            "Could not parse question generation response as JSON."
        ) from exc
    except Exception as exc:
        if isinstance(exc, OpenAIServiceError):
            raise
        raise OpenAIServiceError(f"Question generation failed: {exc}") from exc
