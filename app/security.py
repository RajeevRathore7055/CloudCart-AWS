import secrets
from urllib.parse import quote
from fastapi import HTTPException, Request


class RedirectException(Exception):
    def __init__(self, url: str):
        self.url = url


def flash(request: Request, message: str, category: str = "info"):
    request.session["flash"] = request.session.get("flash", []) + [[category, message]]


def get_current_user(request: Request):
    uid = request.session.get("user_id")
    if not uid:
        return None
    return {"id": uid, "name": request.session.get("name"), "role": request.session.get("role")}


def login_required(request: Request):
    user = get_current_user(request)
    if not user:
        flash(request, "Please login to continue.", "error")
        raise RedirectException("/login?next=" + quote(request.url.path))
    return user


def admin_required(request: Request):
    user = login_required(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    return user


def safe_next(url: str, default: str = "/") -> str:
    """Only allow local redirects (prevents open-redirect attacks)."""
    if url and url.startswith("/") and not url.startswith("//"):
        return url
    return default


def get_csrf_token(request: Request) -> str:
    """One random token per session; every POST form must send it back."""
    token = request.session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        request.session["csrf"] = token
    return token


async def verify_csrf(request: Request):
    """Global dependency: rejects POST/PUT/PATCH/DELETE without a valid CSRF token."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return
    sent = request.headers.get("x-csrf-token")
    if not sent:
        form = await request.form()
        sent = form.get("csrf_token")
    expected = request.session.get("csrf")
    if not expected or not sent or not secrets.compare_digest(str(sent), expected):
        raise HTTPException(status_code=403, detail="Security check failed. Please reload the page and try again.")
