import time


class AuthRequired(Exception):
    pass


def is_expired(data: dict) -> bool:
    cookies = {c["name"]: c for c in data.get("cookies", [])}
    now = time.time()
    for name in ("sso", "sso-rw"):
        cookie = cookies.get(name)
        if not cookie or cookie.get("expires", 0) < now:
            return True
    return False
