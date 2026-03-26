import asyncio
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m grok_research_mcp <auth|serve>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "auth":
        from grok_research_mcp.auth.browser import capture
        from grok_research_mcp.auth.store import save, _auth_path

        print("Opening browser — log in to grok.com, then close or wait...")
        data = asyncio.run(capture())
        save(data)
        print(f"Auth saved to {_auth_path()}")

    elif command == "serve":
        from grok_research_mcp.server import run
        run()

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
