# Aeon CAT Quiz Generator

A Flask web app that:
1. Accepts either an Aeon article URL or pasted article text.
2. Scrapes and cleans article content with `requests` + `BeautifulSoup` when URL mode is used.
3. Supports OpenAI and Google Gemini for paragraph extraction + question generation.
4. Generates 5 CAT-style MCQs from those paragraphs.
5. Renders quiz + scoring UI with answer review and scoring.

## Project Structure

```text
/project
  app.py
  scraper.py
  openai_service.py
  gemini_service.py
  templates/
    index.html
    quiz.html
    results.html
  static/
    style.css
  requirements.txt
```

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set environment variables:
   ```bash
   # OpenAI mode
   export OPENAI_API_KEY="your_openai_api_key_here"
   export OPENAI_MODEL="gpt-4o-mini"

   # Gemini mode
   export GEMINI_API_KEY="your_gemini_api_key_here"
   export GEMINI_MODEL="gemini-1.5-flash"

   # Optional runtime settings
   export FLASK_HOST="0.0.0.0"
   export FLASK_PORT="5000"
   ```
4. Run the app:
   ```bash
   python app.py
   ```
5. Open in browser:
   ```
   http://localhost:5000
   ```

## Example OpenAI Prompts

### Paragraph extraction prompt (used in code)

```text
You are an expert reading-comprehension assistant.
From the article text below, identify the 4 most important paragraphs that best capture:
1) the central thesis,
2) key supporting arguments,
3) nuanced reasoning,
4) conclusion/implications.
Return strictly valid JSON in this shape:
{
  "paragraphs": ["paragraph1", "paragraph2", "paragraph3", "paragraph4"]
}
```

### Question generation prompt (used in code)

```text
You are an IIM CAT verbal ability and reading comprehension question setter.
Using only the paragraphs below, generate exactly 5 CAT-style multiple-choice questions.
Distribute question types across:
- Reading comprehension
- Logical inference
- Vocabulary in context
- Critical reasoning
- Main idea identification

Return strictly valid JSON in this format:
{
  "questions": [
    {
      "question": "...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "A",
      "incorrect_explanation": "Why common wrong choices are wrong.",
      "correct_explanation": "Why the correct choice is best."
    }
  ]
}
```

## Notes
- Invalid URLs, very short pasted text, and scrape failures are handled and surfaced on the homepage.
- Choose AI provider (`OpenAI` or `Google Gemini`) from the homepage before generating a quiz.
- API JSON shape follows the requested schema with both incorrect and correct explanations per question.
- A loading indicator appears after form submission while quiz generation runs.
