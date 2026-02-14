import re

import requests
from bs4 import BeautifulSoup

from app.schemas.item import AutofillResponse


def scrape_url(url: str) -> AutofillResponse:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException:
        return AutofillResponse()

    soup = BeautifulSoup(resp.text, "html.parser")

    title = _get_meta(soup, "og:title") or _get_tag(soup, "title")
    description = _get_meta(soup, "og:description") or _get_meta(soup, "description")
    image_url = _get_meta(soup, "og:image")
    price = _extract_price(soup)

    return AutofillResponse(
        title=title,
        description=description,
        image_url=image_url,
        price=price,
    )


def _get_meta(soup: BeautifulSoup, property_name: str) -> str | None:
    tag = soup.find("meta", attrs={"property": property_name}) or soup.find(
        "meta", attrs={"name": property_name}
    )
    if tag:
        return tag.get("content")
    return None


def _get_tag(soup: BeautifulSoup, tag_name: str) -> str | None:
    tag = soup.find(tag_name)
    return tag.get_text(strip=True) if tag else None


def _extract_price(soup: BeautifulSoup) -> float | None:
    price_meta = _get_meta(soup, "og:price:amount") or _get_meta(soup, "product:price:amount")
    if price_meta:
        try:
            return float(price_meta.replace(",", ".").replace(" ", ""))
        except ValueError:
            pass

    # Try JSON-LD
    for script in soup.find_all("script", type="application/ld+json"):
        text = script.get_text()
        match = re.search(r'"price"\s*:\s*"?([\d.,\s]+)"?', text)
        if match:
            try:
                return float(match.group(1).replace(",", ".").replace(" ", ""))
            except ValueError:
                pass

    return None
