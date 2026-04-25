import asyncio
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m grok_research_mcp <auth|serve|query>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "auth":
        import sys as _sys
        from grok_research_mcp.auth.browser import capture
        from grok_research_mcp.auth.store import save

        print("Opening browser — log in to grok.com, then close or wait...")
        data = asyncio.run(capture())
        save(data)
        if _sys.platform == "win32":
            from grok_research_mcp.auth.store_win32 import _auth_path
            print(f"Auth saved to {_auth_path()}")
        else:
            print("Auth saved to Keychain (grok-research-mcp)")

    elif command == "serve":
        from grok_research_mcp.server import run
        run()

    elif command == "query":
        import argparse
        parser = argparse.ArgumentParser(prog="python -m grok_research_mcp query")
        parser.add_argument("--mode", choices=["web", "x"], default="web")
        parser.add_argument("--reasoning", action="store_true", default=False)
        parser.add_argument("query_text", nargs="+")
        args = parser.parse_args(sys.argv[2:])
        query = " ".join(args.query_text)

        from grok_research_mcp.tools.research import grok_web_search, grok_x_search
        fn = grok_web_search if args.mode == "web" else grok_x_search
        result = asyncio.run(fn(query, is_reasoning=args.reasoning))

        if result.startswith("Error:"):
            print(result, file=sys.stderr)
            sys.exit(1)
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        print(result)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
