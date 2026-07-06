import requests
from bs4 import BeautifulSoup


def scrape_trend_source(url: str) -> dict:
    """Fetch a trend-report page and extract its title + main text content.

    Raises requests.RequestException on network failure — the caller is
    responsible for catching and skipping.
    """
    response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else None

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())

    return {"title": title, "content_text": text}
