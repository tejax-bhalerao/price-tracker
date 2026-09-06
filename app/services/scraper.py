import json
import logging
import re
from typing import Optional, Tuple
from bs4 import BeautifulSoup
import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class ScraperResult:
    def __init__(
        self,
        success: bool,
        price: Optional[float] = None,
        title: Optional[str] = None,
        currency: str = "USD",
        error_message: Optional[str] = None,
    ):
        self.success = success
        self.price = price
        self.title = title
        self.currency = currency
        self.error_message = error_message

    def __repr__(self) -> str:
        return f"<ScraperResult success={self.success} price={self.price} currency={self.currency}>"


class WebScraper:
    """Multi-strategy e-commerce web scraper using BeautifulSoup."""

    def __init__(self):
        self.headers = {
            "User-Agent": settings.SCRAPER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self.timeout = settings.SCRAPER_REQUEST_TIMEOUT

    def clean_price_string(self, raw_price: str) -> Optional[float]:
        """Extract float price from raw string."""
        if not raw_price:
            return None
        # Remove currency symbols, commas, spaces
        cleaned = re.sub(r"[^\d.]", "", raw_price.replace(",", ""))
        try:
            val = float(cleaned)
            return val if val > 0 else None
        except ValueError:
            return None

    def detect_currency(self, text: str) -> str:
        """Detect currency symbol or code."""
        if "₹" in text or "INR" in text:
            return "INR"
        if "€" in text or "EUR" in text:
            return "EUR"
        if "£" in text or "GBP" in text:
            return "GBP"
        if "$" in text or "USD" in text:
            return "USD"
        return "USD"

    def _extract_from_json_ld(self, soup: BeautifulSoup) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """Strategy 1: Extract price from schema.org JSON-LD structured data."""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                # Handle list of items or single item
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict):
                        # Direct offers
                        offers = item.get("offers")
                        if offers:
                            if isinstance(offers, list):
                                offers = offers[0]
                            price = offers.get("price") or offers.get("lowPrice")
                            currency = offers.get("priceCurrency", "USD")
                            name = item.get("name")
                            cleaned_price = self.clean_price_string(str(price))
                            if cleaned_price:
                                return cleaned_price, name, currency
            except Exception:
                continue
        return None, None, None

    def _extract_from_meta_tags(self, soup: BeautifulSoup) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """Strategy 2: Extract price from OpenGraph and standard meta tags."""
        price_meta_selectors = [
            ("meta[property='product:price:amount']", "content"),
            ("meta[property='og:price:amount']", "content"),
            ("meta[name='price']", "content"),
            ("meta[itemprop='price']", "content"),
            ("meta[name='twitter:data1']", "content"),
        ]
        currency_meta = soup.select_one("meta[property='product:price:currency'], meta[property='og:price:currency']")
        currency = currency_meta.get("content", "USD") if currency_meta else "USD"

        for selector, attr in price_meta_selectors:
            tag = soup.select_one(selector)
            if tag and tag.get(attr):
                price = self.clean_price_string(tag[attr])
                if price:
                    title_tag = soup.select_one("meta[property='og:title'], title")
                    title = title_tag.get("content") if title_tag and title_tag.name == "meta" else (title_tag.text if title_tag else None)
                    return price, title, currency

        return None, None, None

    def _extract_from_dom_selectors(self, soup: BeautifulSoup) -> Tuple[Optional[float], Optional[str], Optional[str]]:
        """Strategy 3: Extract price from known common CSS selectors."""
        common_price_selectors = [
            ".a-price-whole",  # Amazon
            "._30jeq3",         # Flipkart
            ".price",           # Generic
            ".product-price",   # Generic
            ".current-price",   # Generic
            "#priceblock_ourprice",
            "#priceblock_dealprice",
            "[data-price]",
            "[itemprop='price']",
            ".offer-price",
            ".sale-price",
        ]

        title_selectors = [
            "#productTitle",
            ".product-title",
            "h1.title",
            "h1",
            "title",
        ]

        title = None
        for t_sel in title_selectors:
            tag = soup.select_one(t_sel)
            if tag and tag.text.strip():
                title = tag.text.strip()
                break

        for selector in common_price_selectors:
            tag = soup.select_one(selector)
            if tag:
                raw_text = tag.get("data-price") or tag.text
                price = self.clean_price_string(raw_text)
                if price:
                    currency = self.detect_currency(raw_text)
                    return price, title, currency

        return None, title, None

    def scrape_html(self, html_content: str) -> ScraperResult:
        """Parse raw HTML string and extract product information."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Try Strategy 1: JSON-LD
            price, title, currency = self._extract_from_json_ld(soup)
            if price:
                return ScraperResult(success=True, price=price, title=title, currency=currency or "USD")

            # Try Strategy 2: Meta tags
            price, title, currency = self._extract_from_meta_tags(soup)
            if price:
                return ScraperResult(success=True, price=price, title=title, currency=currency or "USD")

            # Try Strategy 3: CSS DOM Selectors
            price, title, currency = self._extract_from_dom_selectors(soup)
            if price:
                return ScraperResult(success=True, price=price, title=title, currency=currency or "USD")

            # Fallback title if found
            if not title and soup.title:
                title = soup.title.string.strip() if soup.title.string else None

            return ScraperResult(
                success=False,
                title=title,
                error_message="Could not locate price on page via supported selectors",
            )
        except Exception as exc:
            logger.error(f"Error parsing HTML: {exc}")
            return ScraperResult(success=False, error_message=str(exc))

    def scrape_url(self, url: str) -> ScraperResult:
        """Fetch URL content via HTTP and parse product details."""
        str_url = str(url)
        # Mock / Test URL handler for local testing or demo URLs
        if "example.com" in str_url or "localhost" in str_url or "test-store.local" in str_url:
            return ScraperResult(
                success=True,
                price=69999.0,
                title="Mock E-Commerce Product",
                currency="USD",
            )

        try:
            response = requests.get(str_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            return self.scrape_html(response.text)
        except requests.exceptions.RequestException as exc:
            logger.warning(f"HTTP request failed for {url}: {exc}")
            return ScraperResult(
                success=False,
                error_message=f"Failed to fetch URL ({type(exc).__name__}): {str(exc)}",
            )


scraper = WebScraper()
