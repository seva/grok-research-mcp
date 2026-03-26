import re
from contextlib import asynccontextmanager

import httpx

_GROK_RENDER_TAG = re.compile(r"<grok:render[^>]*>.*?</grok:render>", re.DOTALL)

from grok_research_mcp.auth.store import load, AuthRequired
from grok_research_mcp.client.session import build_session, AuthExpired, AccessDenied
from grok_research_mcp.client.endpoints import send_message, parse_citations


@asynccontextmanager
async def _get_session():
    auth = load()
    async with build_session(auth) as session:
        yield session


def _format_result(text: str, citations: list) -> str:
    if not citations:
        return text
    sources = "\n".join(f"- [{c['title']}]({c['url']})" for c in citations)
    return f"{text}\n\nSources:\n{sources}"


async def _run_query(query: str, mode: str) -> str:
    try:
        async with _get_session() as session:
            text = ""
            citations = []
            async for token, _, model_response in send_message(session, None, query, mode):
                if token:
                    text += token
                if model_response:
                    citations = parse_citations(model_response)
                    canonical = model_response.get("message")
                    if canonical:
                        text = _GROK_RENDER_TAG.sub("", canonical)
            return _format_result(text, citations)
    except (AuthRequired, AuthExpired) as e:
        return f"Error: Auth required. Run: python -m grok_research_mcp auth ({e})"
    except AccessDenied as e:
        return f"Error: Access denied — {e}"
    except httpx.HTTPStatusError as e:
        return f"Error: API returned {e.response.status_code}"
    except httpx.NetworkError as e:
        return f"Error: Network error — {e}"


async def grok_web_search(query: str) -> str:
    return await _run_query(query, "web")


async def grok_x_search(query: str) -> str:
    return await _run_query(query, "x")
