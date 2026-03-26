import asyncio

from playwright.async_api import async_playwright, BrowserContext

GROK_URL = "https://grok.com/sign-in"
POLL_INTERVAL = 2  # seconds
CAPTURE_TIMEOUT = 300  # seconds


def _has_required_cookies(cookies: list) -> bool:
    names = {c["name"] for c in cookies}
    return "sso" in names and "sso-rw" in names


async def capture(timeout: int = CAPTURE_TIMEOUT) -> dict:
    statsig_id = None

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
            ignore_default_args=["--enable-automation"],
        )
        context: BrowserContext = await browser.new_context()
        page = await context.new_page()

        # Intercept outgoing requests to capture x-statsig-id
        def _on_request(request):
            nonlocal statsig_id
            if statsig_id:
                return
            if "grok.com/rest/" in request.url:
                val = request.headers.get("x-statsig-id")
                if val:
                    statsig_id = val

        page.on("request", _on_request)

        await page.goto(GROK_URL)

        # Wait for user to authenticate — poll until required cookies and statsig captured
        elapsed = 0
        while True:
            cookies = await context.cookies()
            if _has_required_cookies(cookies) and statsig_id:
                break
            if elapsed >= timeout:
                await browser.close()
                raise TimeoutError(
                    f"Auth capture timed out after {timeout}s. "
                    "Log in within the browser window before the timeout expires."
                )
            await asyncio.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL

        cookies = await context.cookies()
        await browser.close()

        return {
            "cookies": [
                {"name": c["name"], "value": c["value"], "expires": c.get("expires", -1),
                 "domain": c.get("domain", ""), "path": c.get("path", "/")}
                for c in cookies
            ],
            "statsig_id": statsig_id,
        }
