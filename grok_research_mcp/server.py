import sys

from mcp.server.fastmcp import FastMCP

from grok_research_mcp.auth.store import load, is_expired, AuthRequired
from grok_research_mcp.tools.research import grok_web_search, grok_x_search

mcp = FastMCP("grok-research")


@mcp.tool()
async def grok_web_search_tool(query: str, is_reasoning: bool = False) -> str:
    """Search the web using Grok and return the response with sources.
    Set is_reasoning=True to enable step-by-step thinking mode (slower, more thorough)."""
    return await grok_web_search(query, is_reasoning)


@mcp.tool()
async def grok_x_search_tool(query: str, is_reasoning: bool = False) -> str:
    """Search X (Twitter) posts using Grok and return the response with sources.
    Set is_reasoning=True to enable step-by-step thinking mode (slower, more thorough)."""
    return await grok_x_search(query, is_reasoning)


def run():
    try:
        auth = load()
    except AuthRequired:
        print("Auth required. Run: python -m grok_research_mcp auth", file=sys.stderr)
        sys.exit(1)

    if is_expired(auth):
        print("Auth expired. Run: python -m grok_research_mcp auth", file=sys.stderr)
        sys.exit(1)

    mcp.run(transport="stdio")
