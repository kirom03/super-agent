import os
import json
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
import webbrowser
from bs4 import BeautifulSoup
from core.config import SANDBOX_DIR

def search_web(query: str, max_results: int = 5) -> str:
    """Performs a live web search using DuckDuckGo/DDGS and returns top results with summaries."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href") or r.get("link", ""),
                    "snippet": r.get("body") or r.get("snippet", "")
                })

        if not results:
            return json.dumps({"status": "no_results", "query": query, "message": "Pencarian tidak menemukan hasil."})

        return json.dumps({
            "status": "success",
            "query": query,
            "count": len(results),
            "results": results
        }, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "query": query, "error": str(e)})

def fetch_web_page(url: str, max_chars: int = 6000) -> str:
    """Fetches a webpage, cleans the HTML, and returns the readable text content and title."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        with httpx.Client(timeout=15.0, follow_redirects=True, headers=headers) as client:
            resp = client.get(url)
            if resp.status_code != 200:
                return json.dumps({"status": "error", "url": url, "http_status": resp.status_code, "error": f"Failed with HTTP {resp.status_code}"})

            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove scripts, styles, iframes, ads
            for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav", "aside"]):
                tag.decompose()

            title = soup.title.string.strip() if soup.title and soup.title.string else "Untitled"
            text = soup.get_text(separator="\n", strip=True)

            # Deduplicate multiple blank lines
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            cleaned_text = "\n".join(lines)

            if len(cleaned_text) > max_chars:
                cleaned_text = cleaned_text[:max_chars] + f"\n... [Truncated: {len(cleaned_text) - max_chars} characters omitted]"

            return json.dumps({
                "status": "success",
                "url": url,
                "title": title,
                "content": cleaned_text
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "url": url, "error": str(e)})

def call_rest_api(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
    timeout_sec: float = 20.0
) -> str:
    """Executes a generic HTTP REST API call (GET, POST, PUT, DELETE, PATCH)."""
    try:
        method = method.upper()
        with httpx.Client(timeout=timeout_sec) as client:
            resp = client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_body
            )
            content_type = resp.headers.get("content-type", "")
            try:
                data = resp.json()
                body_str = json.dumps(data, indent=2, ensure_ascii=False)
            except Exception:
                body_str = resp.text[:4000]

            return json.dumps({
                "status": "success",
                "http_status": resp.status_code,
                "url": str(resp.url),
                "headers": dict(resp.headers),
                "body": body_str
            })
    except Exception as e:
        return json.dumps({"status": "error", "url": url, "error": str(e)})

def download_file(url: str, filename: str) -> str:
    """Downloads an external web resource/file directly into the local sandbox directory."""
    try:
        dest_path = Path(SANDBOX_DIR) / filename
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        headers = {"User-Agent": "SuperAgent/1.0"}
        with httpx.Client(timeout=60.0, follow_redirects=True, headers=headers) as client:
            with client.stream("GET", url) as resp:
                if resp.status_code != 200:
                    return json.dumps({"status": "error", "url": url, "error": f"HTTP {resp.status_code}"})
                with open(dest_path, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=8192):
                        f.write(chunk)

        size = dest_path.stat().st_size
        return json.dumps({
            "status": "success",
            "url": url,
            "saved_to": str(dest_path),
            "size_bytes": size,
            "filename": filename
        })
    except Exception as e:
        return json.dumps({"status": "error", "url": url, "error": str(e)})

def open_in_browser(url: str) -> str:
    """Opens a URL or web page directly in the laptop's default browser (Chrome/Edge)."""
    try:
        webbrowser.open(url)
        return json.dumps({
            "status": "success",
            "url": url,
            "message": f"Successfully launched '{url}' in your default browser."
        })
    except Exception as e:
        return json.dumps({"status": "error", "url": url, "error": str(e)})

