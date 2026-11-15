import re
import time
from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import execute, query_one
from app.security import flash, safe_next
from app.templating import render

router = APIRouter(tags=["auth"])
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# Simple brute-force protection: 5 failed logins per email -> locked for 15 minutes.
# (In-memory, per server process. With several EC2 instances use a shared store such as ElastiCache.)
_FAILS = {}
MAX_FAILS, WINDOW = 5, 15 * 60


def _is_locked(email: str) -> bool:
    now = time.time()
    recent = [t for t in _FAILS.get(email, []) if now - t < WINDOW]
    _FAILS[email] = recent
    return len(recent) >= MAX_FAILS


def _start_session(request: Request, user: dict):
    request.session.clear()  # prevents session fixation
    request.session["user_id"] = user["id"]
    request.session["name"] = user["name"]
    request.session["role"] = user["role"]


@router.get("/register")
def register_page(request: Request):
    return render(request, "register.html", form={}, errors=[])


@router.post("/register")
def register(request: Request, name: str = Form(""), email: str = Form(""), password: str = Form(""), confirm: str = Form("")):
    name, email = name.strip(), email.strip().lower()
    errors = []
    if len(name) < 2 or len(name) > 100:
        errors.append("Name must be 2-100 characters.")
    if not EMAIL_RE.match(email) or len(email) > 150:
        errors.append("Enter a valid email address.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if password != confirm:
        errors.append("Passwords do not match.")
    if not errors and query_one("SELECT id FROM users WHERE email=%s", (email,)):
        errors.append("This email is already registered.")
    if errors:
        return render(request, "register.html", status_code=400, form={"name": name, "email": email}, errors=errors)
    uid = execute(
        "INSERT INTO users (name, email, password_hash, role) VALUES (%s,%s,%s,'customer')",
        (name, email, generate_password_hash(password)),
    )
    _start_session(request, {"id": uid, "name": name, "role": "customer"})
    flash(request, f"Welcome to CloudCart, {name}!", "success")
    return RedirectResponse("/", status_code=303)


@router.get("/login")
def login_page(request: Request, next: str = "/"):
    return render(request, "login.html", next=safe_next(next), errors=[], email="")


@router.post("/login")
def login(request: Request, email: str = Form(""), password: str = Form(""), next: str = Form("/")):
    email = email.strip().lower()
    if _is_locked(email):
        return render(request, "login.html", status_code=429, next=safe_next(next), email=email,
                      errors=["Too many failed attempts. Please try again in 15 minutes."])
    row = query_one("SELECT id, name, role, password_hash FROM users WHERE email=%s", (email,))
    if not row or not check_password_hash(row["password_hash"], password):
        _FAILS.setdefault(email, []).append(time.time())
        return render(request, "login.html", status_code=401, next=safe_next(next), email=email, errors=["Invalid email or password."])
    _FAILS.pop(email, None)
    _start_session(request, row)
    flash(request, f"Welcome back, {row['name']}!", "success")
    if row["role"] == "admin" and next in ("/", ""):
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse(safe_next(next), status_code=303)


@router.get("/logout")
def logout_get():
    # Logging out changes state, so it must be a POST (with CSRF token). GET only redirects.
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "You have been logged out.", "info")
    return RedirectResponse("/", status_code=303)
