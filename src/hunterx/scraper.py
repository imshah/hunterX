import re

import httpx
from bs4 import BeautifulSoup, Tag

_JD_SELECTORS = [
    ".description__text",
    ".show-more-less-html__markup",
    "#jobDescriptionText",
    ".jobsearch-jobDescriptionText",
    "#content .posting-page",
    ".posting-page",
    "[class*='job-description']",
    "[class*='jobDescription']",
    "[class*='job_description']",
    "[id*='job-description']",
    "[id*='jobDescription']",
    "[id*='job_description']",
    "article",
    "main",
    "[role='main']",
]

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

_MIN_TEXT_LENGTH = 100


def fetch_job_description(url: str, timeout: float = 30.0) -> str:
    response = httpx.get(url, headers=_HEADERS, timeout=timeout, follow_redirects=True)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    for tag in soup.find_all(["script", "style", "nav", "header", "footer", "noscript"]):
        tag.decompose()

    for selector in _JD_SELECTORS:
        element = soup.select_one(selector)
        if element and len(element.get_text(strip=True)) > _MIN_TEXT_LENGTH:
            return _clean_text(element)

    body = soup.find("body")
    if body:
        return _clean_text(body)

    return _clean_text(soup)


def _clean_text(element: Tag) -> str:
    text = element.get_text(separator="\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(lines).strip()
