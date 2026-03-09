from typing import Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class ScraperError(ValueError):
    """Raised when an article cannot be scraped or validated."""


def _validate_aeon_url(url: str) -> None:
    """Ensure URL points to Aeon and has a supported scheme."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ScraperError("Invalid URL scheme. Use http:// or https://.")
    if "aeon.co" not in parsed.netloc:
        raise ScraperError("Please provide a valid Aeon article URL.")


def scrape_aeon_article(url: str) -> Tuple[str, str]:
    """Fetch and extract article title + meaningful text from an Aeon URL."""
    _validate_aeon_url(url)

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ScraperError(f"Could not fetch article: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")

    # Title extraction with fallbacks.
    title = ""
    if soup.find("meta", property="og:title"):
        title = soup.find("meta", property="og:title").get("content", "").strip()
    if not title and soup.title:
        title = soup.title.get_text(strip=True)

    # Aeon usually stores article content under <article> with paragraph children.
    article_tag = soup.find("article")
    paragraph_elements = []

    if article_tag:
        paragraph_elements = article_tag.find_all("p")

    # Fallback selectors for resilience across page variations.
    if not paragraph_elements:
        paragraph_elements = soup.select("main p, .article-body p, .essay__content p")

    cleaned_paragraphs = []
    for p in paragraph_elements:
        text = p.get_text(" ", strip=True)
        if len(text) < 40:
            continue
        lowered = text.lower()
        if any(
            marker in lowered
            for marker in ["newsletter", "subscribe", "advertisement", "read more"]
        ):
            continue
        cleaned_paragraphs.append(text)

    if not cleaned_paragraphs:
        raise ScraperError(
            "Unable to extract article paragraphs from this URL. Please try another Aeon article."
        )

    article_text = "\n\n".join(cleaned_paragraphs)
    if not title:
        title = "Aeon Article"

    return title, article_text
