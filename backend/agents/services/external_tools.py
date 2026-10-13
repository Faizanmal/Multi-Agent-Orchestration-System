import logging
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def web_search(query: str) -> dict[str, Any]:
    """
    Search the web for information using DuckDuckGo Lite.
    Useful for answering questions about current events, facts, or fetching live data.
    """
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))

        if not results:
            return {"status": "success", "results": "No results found."}

        formatted_results = []
        for r in results:
            formatted_results.append(
                {
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "href": r.get("href", ""),
                }
            )

        return {"status": "success", "results": formatted_results}
    except ImportError:
        # Fallback if duckduckgo_search is not installed
        return {
            "status": "error",
            "error": "duckduckgo_search package is missing. Please run: pip install duckduckgo-search",
        }
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": f"Search failed: {e!s}"}


@tool
def calculate(expression: str) -> dict[str, Any]:
    """
    Evaluate a mathematical expression.
    Supports basic arithmetic (+, -, *, /) and parentheses.
    Use this instead of doing math in your head to avoid mistakes.
    Example expression: "25 * (4.5 + 1.2)"
    """
    try:
        import ast
        import operator

        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        def _eval(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return allowed_operators[type(node.op)](
                    _eval(node.left), _eval(node.right)
                )
            elif isinstance(node, ast.UnaryOp):
                return allowed_operators[type(node.op)](_eval(node.operand))
            else:
                raise TypeError(
                    f"Unsupported mathematical expression element: {type(node)}"
                )

        # Parse and evaluate safely
        result = _eval(ast.parse(expression, mode="eval").body)
        return {"status": "success", "expression": expression, "result": float(result)}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": f"Invalid expression: {e!s}"}


@tool
def get_current_datetime(timezone_str: str = "UTC") -> dict[str, Any]:
    """
    Get the current date and time.
    """
    try:
        now = datetime.now(timezone.utc)
        return {
            "status": "success",
            "utc_iso": now.isoformat(),
            "formatted": now.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": str(e)}


@tool
def fetch_url_content(url: str) -> dict[str, Any]:
    """
    Fetch the raw text content from a specific URL.
    Useful for reading articles, documentation, or extracting text from a webpage.
    """
    try:
        import urllib.request

        from bs4 import BeautifulSoup

        req = urllib.request.Request(
            url, data=None, headers={"User-Agent": "Mozilla/5.0 Multi-Agent-Orch"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            html = response.read().decode("utf-8")

        soup = BeautifulSoup(html, "html.parser")

        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text(separator=" ", strip=True)
        # Limit to first 5000 chars to avoid context overflow
        return {"status": "success", "url": url, "content": text[:5000]}
    except ImportError:
        return {"status": "error", "error": "beautifulsoup4 package is missing."}
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error": f"Failed to fetch URL: {e!s}"}


# List of all external tools to be imported by the coordinator
EXTERNAL_TOOLS = [web_search, calculate, get_current_datetime, fetch_url_content]
