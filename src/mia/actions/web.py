"""
Web search & page reading tools.

Default: DuckDuckGo (free, no API key).
Optional: Google Custom Search (requires API key + CX ID).
"""

from __future__ import annotations

import os
import json
import re
from urllib.request import urlopen, Request
from urllib.error import URLError
from html.parser import HTMLParser


# ------------------------------------------------------------------
# Web search
# ------------------------------------------------------------------

def web_search(query: str, provider: str = "duckduckgo", max_results: int = 5) -> str:
    """Search the web and return top results with titles and snippets."""
    if provider == "google":
        return _google_search(query, max_results)
    return _duckduckgo_search(query, max_results)


def _duckduckgo_search(query: str, max_results: int = 5) -> str:
    """Search using ddgs (DuckDuckGo search) library."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        if not results:
            return f"No results found for '{query}'."

        output = []
        for i, r in enumerate(results, 1):
            title = r.get("title", "No title")
            url = r.get("href", r.get("link", ""))
            snippet = r.get("body", r.get("snippet", ""))
            output.append(f"{i}. **{title}**\n   URL: {url}\n   {snippet}")

        return f"Search results for '{query}':\n\n" + "\n\n".join(output)

    except ImportError:
        return "Error: ddgs package not installed. Run: pip install ddgs"
    except Exception as e:
        return f"Search error: {e}"


def _google_search(query: str, max_results: int = 5) -> str:
    """Search using Google Custom Search API (requires GOOGLE_SEARCH_API_KEY + GOOGLE_SEARCH_CX)."""
    api_key = os.environ.get("GOOGLE_SEARCH_API_KEY")
    cx = os.environ.get("GOOGLE_SEARCH_CX")

    if not api_key or not cx:
        return "Google Search not configured. Set GOOGLE_SEARCH_API_KEY and GOOGLE_SEARCH_CX, or use DuckDuckGo."

    try:
        from urllib.parse import urlencode
        params = urlencode({
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": max_results,
        })
        url = f"https://www.googleapis.com/customsearch/v1?{params}"
        req = Request(url, headers={"User-Agent": "Mia-Assistant/1.0"})
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        items = data.get("items", [])
        if not items:
            return f"No Google results found for '{query}'."

        output = []
        for i, item in enumerate(items, 1):
            title = item.get("title", "No title")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            output.append(f"{i}. **{title}**\n   URL: {link}\n   {snippet}")

        return f"Google search results for '{query}':\n\n" + "\n\n".join(output)

    except Exception as e:
        return f"Google search error: {e}"


# ------------------------------------------------------------------
# Webpage reader
# ------------------------------------------------------------------

class _TextExtractor(HTMLParser):
    """Simple HTML → text extractor. Skips script/style tags."""

    def __init__(self):
        super().__init__()
        self._skip_tags = {"script", "style", "noscript", "head"}
        self._skip_depth = 0
        self.text_parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self._skip_tags:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag.lower() in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth == 0:
            text = data.strip()
            if text:
                self.text_parts.append(text)


def read_webpage(url: str) -> str:
    """Fetch a URL and extract the main text content."""
    try:
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        req = Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mia-Assistant/1.0",
        })
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")

        # Extract text
        extractor = _TextExtractor()
        extractor.feed(html)
        text = "\n".join(extractor.text_parts)

        # Collapse whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Truncate if too long
        max_chars = 8000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n...[truncated]"

        return f"Content from {url}:\n\n{text}" if text.strip() else f"Could not extract text from {url}."

    except URLError as e:
        return f"Failed to fetch {url}: {e}"
    except Exception as e:
        return f"Error reading webpage: {e}"
