# grok-research-mcp

MCP server exposing Grok web and X search to any MCP client. Uses your existing Grok session via cookie auth + DPAPI encryption.

## Install

```
pip install grok-research-mcp
playwright install chromium
```

Or with uv:

```
uv pip install grok-research-mcp
playwright install chromium
```

## Auth

Run once. Opens a Chrome window to `grok.com/sign-in` — log in, then wait for the window to close automatically.

```
python -m grok_research_mcp auth
```

Credentials are stored encrypted at `~/.grok-mcp/auth.dpapi` (Windows DPAPI, current user only).

Re-run when your session expires.

## MCP Client Config

### Claude Code (`~/.claude.json`)

```json
{
  "mcpServers": {
    "grok-research": {
      "command": "python",
      "args": ["-m", "grok_research_mcp", "serve"]
    }
  }
}
```

### Cursor (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "grok-research": {
      "command": "python",
      "args": ["-m", "grok_research_mcp", "serve"]
    }
  }
}
```

### Cline (VS Code settings)

```json
{
  "cline.mcpServers": {
    "grok-research": {
      "command": "python",
      "args": ["-m", "grok_research_mcp", "serve"]
    }
  }
}
```

## Tools

| Tool | Description |
|---|---|
| `grok_web_search_tool` | Searches the web via Grok. Returns response text + sources. |
| `grok_x_search_tool` | Searches X posts via Grok. Returns response text + sources. |

## Requirements

- Windows (DPAPI auth storage)
- Python 3.11+
- Active Grok subscription
