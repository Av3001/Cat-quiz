# CAT Quiz Generator (Pasted Text)

A Flask web app that:
1. Accepts pasted article text.
2. Uses OpenAI or Google Gemini to identify the 4 most important paragraphs.
3. Generates 5 CAT-style MCQs from those paragraphs.
4. Shows score and answer explanations after submission.

## Project Structure

```text
/project
  app.py
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

## Error Handling
- Empty text is rejected with a clear message.
- Very short text is rejected with minimum length feedback.
- Invalid AI provider values are rejected.
- Model/JSON failures are surfaced as provider-specific AI errors.
- Invalid quiz submission payloads are handled and the user is asked to regenerate.

## Notes
- URL scraping has been removed; this app is now pasted-text-only.
- Quiz output includes both incorrect and correct explanations per question.
