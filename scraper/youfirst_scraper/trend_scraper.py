import xml.etree.ElementTree as ET

import requests
from bs4 import BeautifulSoup


def _parse_rss(xml_text: str) -> dict:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    title = channel.findtext("title") if channel is not None else None

    lines = []
    for item in root.iter("item"):
        item_title = (item.findtext("title") or "").strip()
        extras = []
        for el in item.iter():
            tag = el.tag.split("}")[-1]
            if tag in ("news_item_title", "description") and el.text and el.text.strip():
                extras.append(BeautifulSoup(el.text, "html.parser").get_text().strip())
        if item_title:
            line = f"- {item_title}"
            if extras:
                line += f" — {'; '.join(extras)}"
            lines.append(line)

    return {"title": title, "content_text": "\n".join(lines)}


def scrape_trend_source(url: str) -> dict:
    """Fetch a trend source (RSS or HTML page) and extract its title + main content.

    Raises requests.RequestException on network failure — the caller is
    responsible for catching and skipping.
    """
    response = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()

    body = response.text
    content_type = response.headers.get("Content-Type", "")
    if "xml" in content_type or body.lstrip().startswith(("<?xml", "<rss")):
        return _parse_rss(body)

    soup = BeautifulSoup(body, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else None

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = " ".join(soup.get_text(separator=" ").split())

    return {"title": title, "content_text": text}
