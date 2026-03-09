import os
from flask import Flask, render_template, request

from scraper import scrape_aeon_article
from openai_service import (
    OpenAIServiceError,
    extract_key_paragraphs,
    generate_cat_questions,
)
from gemini_service import (
    GeminiServiceError,
    extract_key_paragraphs_gemini,
    generate_cat_questions_gemini,
)

app = Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    """Render the homepage with the URL submission form."""
    return render_template("index.html", provider="openai")


@app.route("/generate", methods=["POST"])
def generate_quiz():
    """Handle form submission, create quiz payload, and render quiz page."""
    article_url = request.form.get("article_url", "").strip()
    article_text_input = request.form.get("article_text", "").strip()
    provider = request.form.get("provider", "openai").strip().lower()

    if not article_url and not article_text_input:
        return render_template(
            "index.html",
            error="Please provide an Aeon article URL or paste article text.",
            provider=provider,
        )

    try:
        if article_text_input:
            if len(article_text_input) < 250:
                return render_template(
                    "index.html",
                    error="Pasted text is too short. Please provide a fuller article excerpt.",
                    provider=provider,
                )
            article_title = "Pasted Article Text"
            article_text = article_text_input
            source_url = ""
        else:
            article_title, article_text = scrape_aeon_article(article_url)
            source_url = article_url

        if provider == "gemini":
            paragraphs = extract_key_paragraphs_gemini(article_text)
            questions = generate_cat_questions_gemini(paragraphs)
        else:
            paragraphs = extract_key_paragraphs(article_text)
            questions = generate_cat_questions(paragraphs)
    except ValueError as exc:
        return render_template("index.html", error=str(exc), provider=provider)
    except (OpenAIServiceError, GeminiServiceError) as exc:
        return render_template(
            "index.html",
            error=f"AI generation error ({provider}): {exc}",
            provider=provider,
        )
    except Exception as exc:  # Defensive fallback for unexpected runtime issues.
        return render_template(
            "index.html",
            error=f"Unexpected error while generating quiz: {exc}",
            provider=provider,
        )

    return render_template(
        "quiz.html",
        title=article_title,
        url=source_url,
        paragraphs=paragraphs,
        questions=questions,
    )


@app.route("/submit", methods=["POST"])
def submit_quiz():
    """Evaluate the submitted quiz and render the results page."""
    title = request.form.get("title", "Aeon Article Quiz")
    paragraphs = request.form.getlist("paragraphs")
    question_count = int(request.form.get("question_count", 0))

    results = []
    score = 0

    for index in range(question_count):
        question_text = request.form.get(f"question_{index}", "")
        user_answer = request.form.get(f"answer_{index}", "")
        correct_answer = request.form.get(f"correct_{index}", "")

        options = {
            "A": request.form.get(f"option_{index}_A", ""),
            "B": request.form.get(f"option_{index}_B", ""),
            "C": request.form.get(f"option_{index}_C", ""),
            "D": request.form.get(f"option_{index}_D", ""),
        }

        correct_explanation = request.form.get(f"correct_expl_{index}", "")
        incorrect_explanation = request.form.get(f"incorrect_expl_{index}", "")

        is_correct = user_answer == correct_answer
        if is_correct:
            score += 1

        results.append(
            {
                "question": question_text,
                "options": options,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "correct_explanation": correct_explanation,
                "incorrect_explanation": incorrect_explanation,
            }
        )

    return render_template(
        "results.html",
        title=title,
        paragraphs=paragraphs,
        results=results,
        score=score,
        total=question_count,
    )


if __name__ == "__main__":
    # Read host/port from env for deployment flexibility.
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=True)
