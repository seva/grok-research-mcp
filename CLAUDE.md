# grok-research-mcp

MCP server exposing Grok web research tools to any MCP client via cookie auth + platform keychain (Keychain on macOS, DPAPI on Windows).

## Session Start
1. Read METHODOLOGY.md
2. Scan IMPLEMENTATION.md checkboxes — first unchecked task is current state
3. Check open GitHub issues for failures and decisions
4. Search MCP memory for relevant prior knowledge (`mcp__memory__retrieve_memory`)

## Installed clients (this machine)
- **OpenCode** — `~/.config/opencode/opencode.json`, venv python at `~/projects/grok-research-mcp/.venv/bin/python`
- Auth stored in macOS Keychain under service `grok-research-mcp`. Re-run auth when session expires: `python -m grok_research_mcp auth`

## Conventions
- Multi-line bash strings: use heredoc `$(cat <<'EOF'\n...\nEOF\n)` — avoids quoting issues on Windows bash
