# grok-research-mcp

MCP server exposing Grok web and X search to any MCP client. Uses your existing Grok session via cookie auth + platform keychain.

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

Credentials are stored in the platform keychain (macOS Keychain or Windows DPAPI), bound to the current user.

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

## OpenClaw / exec-based agents

For agents that use the exec tool, use the `query` subcommand directly — no MCP client support needed.

### Prerequisites

Auth must be set up once on the same machine the agent runs on:

```
python -m grok_research_mcp auth
```

### Usage

```
python -m grok_research_mcp query "current state of LLM agent memory architectures"
python -m grok_research_mcp query --mode x "xAI Grok outage"
```

- Exit 0 — result on stdout
- Exit 1 — error message on stderr (auth expired, network failure, Grok down)

### openclaw.json

Exec must be enabled with `ask: off` for unattended use. If `python` is not in the gateway's PATH, add it via `pathPrepend`:

```json5
"tools": {
  "exec": {
    "host": "gateway",
    "security": "full",
    "ask": "off",
    "pathPrepend": ["C:/Users/<you>/AppData/Local/Programs/Python/Python311"]
  }
}
```

## Tools

| Tool | Description |
|---|---|
| `grok_web_search_tool` | Searches the web via Grok. Returns response text + sources. |
| `grok_x_search_tool` | Searches X posts via Grok. Returns response text + sources. |

## Terms of Use

This tool is intended for personal research use by individuals with an active Grok subscription. See [TERMS.md](TERMS.md).

## Requirements

- Windows 10/11 or macOS
- Python 3.11+
- Active Grok subscription

## Platform support

| Platform | Credential storage |
|---|---|
| macOS | Keychain via `keyring` |
| Windows | DPAPI (`CryptProtectData` / `CryptUnprotectData`) |
| Linux | Not yet supported |
