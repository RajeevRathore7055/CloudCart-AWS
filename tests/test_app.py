"""CloudCart tests. Run:  pytest -v   (needs MySQL running + `python -m scripts.init_db` done)"""
import io
import os
import re
import uuid

import pytest
from fastapi.testclient import TestClient

from app.db import execute, query_one
from app.main import app

PASSWORD = "Test@1234"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@cloudcart.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@123")


def token(c):
    """Read the CSRF token of the current session from any page."""
    html = c.get("/login").text
    return re.search(r'name="csrf-token" content="([^"]+)"', html).group(1)


def post(c, url, data=None, **kw):
    data = dict(data or {})
    data["csrf_token"] = token(c)
    return c.post(url, data=data, **kw)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def email():
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


@pytest.fixture(scope="module")
def admin():
    with TestClient(app) as c:
        r = post(c, "/login", {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        assert r.status_code == 200 and "Welcome back" in r.text
        yield c


# ---------------- system / security ----------------
def test_health():
    with TestClient(app) as c:
        assert c.get("/health").json() == {"status": "ok", "database": "up"}


def test_security_headers():
    with TestClient(app) as c:
        h = c.get("/").headers
        assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY"
        assert "frame-ancestors 'none'" in h["content-security-policy"]


def test_csrf_blocks_post_without_token():
    with TestClient(app) as c:
        c.get("/login")
        r = c.post("/login", data={"email": "a@b.com", "password": "x"})
        assert r.status_code == 403 and "Security check failed" in r.text


def test_csrf_blocks_wrong_token():
    with TestClient(app) as c:
        c.get("/login")
        assert c.post("/login", data={"email": "a@b.com", "password": "x", "csrf_token": "forged"}).status_code == 403


def test_sql_injection_is_harmless(client):
    r = client.get("/products", params={"q": "' OR '1'='1"})
    assert r.status_code == 200 and "No products match" in r.text


def test_login_throttle_after_repeated_failures():
    target = f"nobody_{uuid.uuid4().hex[:6]}@example.com"
    with TestClient(app) as c:
        for _ in range(5):
            assert post(c, "/login", {"email": target, "password": "wrong"}).status_code == 401
        r = post(c, "/login", {"email": target, "password": "wrong"})
        assert r.status_code == 429 and "Too many failed attempts" in r.text


# ---------------- auth ----------------
def test_register(client, email):
    r = post(client, "/register", {"name": "Test User", "email": email, "password": PASSWORD, "confirm": PASSWORD})
    assert r.status_code == 200 and "Welcome to CloudCart" in r.text
    row = query_one("SELECT password_hash FROM users WHERE email=%s", (email,))
    assert row and row["password_hash"] != PASSWORD  # hashed, not plain text


def test_register_duplicate_email(email):
    with TestClient(app) as c:
        r = post(c, "/register", {"name": "X Y", "email": email, "password": PASSWORD, "confirm": PASSWORD})
        assert r.status_code == 400 and "already registered" in r.text


def test_register_validation():
    with TestClient(app) as c:
        r = post(c, "/register", {"name": "A", "email": "bad", "password": "123", "confirm": "456"})
        assert r.status_code == 400 and "valid email" in r.text and "do not match" in r.text


def test_invalid_login():
    with TestClient(app) as c:
        r = post(c, "/login", {"email": "nobody@example.com", "password": "wrong"})
        assert r.status_code == 401 and "Invalid email or password" in r.text


def test_login_and_logout(email):
    with TestClient(app) as c:
        assert "Welcome back" in post(c, "/login", {"email": email, "password": PASSWORD}).text
        assert "Logout" in c.get("/").text
        assert c.get("/logout", follow_redirects=False).status_code == 303   # GET must NOT log out
        assert "Logout" in c.get("/").text
        post(c, "/logout")                                                  # POST with token logs out
        assert "Login" in c.get("/").text


# ---------------- catalogue / API ----------------
def test_product_search_and_filter(client):
    assert "UltraBook" in client.get("/products?q=laptop").text
    assert "No products match" in client.get("/products?q=zzzzzz").text
    assert "Backpack" in client.get("/products?category=6").text
    prices = [float(i["price"]) for i in client.get("/api/products?sort=price_asc").json()]
    assert prices == sorted(prices)


def test_product_api_detail_and_404(client):
    first = client.get("/api/products").json()[0]
    one = client.get(f"/api/products/{first['id']}").json()
    assert one["name"] == first["name"] and "image" in one
    assert client.get("/api/products/999999").status_code == 404


def test_product_detail_page_and_missing(client):
    assert client.get("/products/1").status_code == 200
    assert client.get("/products/999999").status_code == 404


# ---------------- cart / checkout ----------------
def test_cart_requires_login():
    with TestClient(app) as c:
        r = c.get("/cart", follow_redirects=False)
        assert r.status_code == 303 and r.headers["location"].startswith("/login")


def test_cart_checkout_and_order(client):
    first = client.get("/api/products?q=Mouse").json()[0]
    pid, stock_before = first["id"], first["stock"]
    post(client, f"/cart/add/{pid}", {"quantity": 2})
    assert "GlideX" in client.get("/cart").text
    post(client, f"/cart/update/{pid}", {"action": "inc"})
    post(client, f"/cart/update/{pid}", {"action": "dec"})
    post(client, f"/cart/remove/{pid}")
    assert "Your cart is empty" in client.get("/cart").text

    post(client, f"/cart/add/{pid}", {"quantity": 2})
    assert post(client, "/checkout", {"name": "A", "address": "short", "phone": "abc"}).status_code == 400
    r = post(client, "/checkout", {"name": "Test User", "address": "12 Park Street, Dehradun", "phone": "9876543210"})
    assert r.status_code == 200 and "Order Confirmed" in r.text
    assert "Placed" in client.get("/orders").text
    assert query_one("SELECT stock FROM products WHERE id=%s", (pid,))["stock"] == stock_before - 2


def test_cannot_add_more_than_stock(client):
    p = client.get("/api/products?q=Mouse").json()[0]
    r = post(client, f"/cart/add/{p['id']}", {"quantity": p["stock"] + 50})
    assert "in stock" in r.text
    assert "Your cart is empty" in client.get("/cart").text


def test_missing_order_returns_404(client):
    assert client.get("/orders/999999").status_code == 404


# ---------------- admin ----------------
def test_customer_cannot_open_admin(client):
    assert client.get("/admin").status_code == 403


def test_admin_login_and_dashboard(admin):
    r = admin.get("/admin")
    assert r.status_code == 200 and "Total Sales" in r.text and "Top Products" in r.text


def test_admin_pages_open(admin):
    for url in ("/admin/products", "/admin/users", "/admin/orders", "/admin/products/new"):
        assert admin.get(url).status_code == 200


def test_admin_add_edit_delete_product(admin):
    name = "Test Product " + uuid.uuid4().hex[:6]
    r = post(admin, "/admin/products/new", {"name": name, "category_id": "1", "price": "999.50", "stock": "5", "description": "demo"})
    assert r.status_code == 200 and name in r.text
    pid = query_one("SELECT id FROM products WHERE name=%s", (name,))["id"]
    post(admin, f"/admin/products/{pid}/edit", {"name": name, "category_id": "1", "price": "1200", "stock": "7", "description": "demo"})
    assert float(query_one("SELECT price FROM products WHERE id=%s", (pid,))["price"]) == 1200.0
    post(admin, f"/admin/products/{pid}/delete")
    assert query_one("SELECT id FROM products WHERE id=%s", (pid,)) is None


def test_admin_rejects_bad_image(admin):
    r = post(admin, "/admin/products/new", {"name": "Bad", "category_id": "1", "price": "1", "stock": "1"},
             files={"image": ("x.exe", io.BytesIO(b"abc"), "application/octet-stream")})
    assert r.status_code == 400 and "Only JPG" in r.text


def test_admin_image_upload_and_cleanup(admin):
    from app.services.storage import IMAGES_DIR
    name = "Img Product " + uuid.uuid4().hex[:6]
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 64
    r = post(admin, "/admin/products/new", {"name": name, "category_id": "1", "price": "10", "stock": "1"},
             files={"image": ("p.png", io.BytesIO(png), "image/png")})
    assert r.status_code == 200
    row = query_one("SELECT id, image_url FROM products WHERE name=%s", (name,))
    assert (IMAGES_DIR / row["image_url"]).exists()
    post(admin, f"/admin/products/{row['id']}/delete")
    assert not (IMAGES_DIR / row["image_url"]).exists()      # uploaded file is cleaned up


def test_admin_update_order_status(admin):
    order = query_one("SELECT id FROM orders ORDER BY id DESC LIMIT 1")
    assert order, "run test_cart_checkout_and_order first"
    post(admin, f"/admin/orders/{order['id']}/status", {"status": "Shipped"})
    assert query_one("SELECT status FROM orders WHERE id=%s", (order["id"],))["status"] == "Shipped"
    assert post(admin, f"/admin/orders/{order['id']}/status", {"status": "Hacked"}).status_code == 400


# ---------------- storage / S3 ----------------
def test_image_url_builder(monkeypatch):
    from app.config import settings
    from app.services import storage
    monkeypatch.setattr(settings, "IMAGE_BASE_URL", "")
    monkeypatch.setattr(settings, "S3_BUCKET_NAME", "")
    assert storage.image_url("laptop.svg") == "/static/images/laptop.svg"
    assert storage.image_url(None).endswith("placeholder.svg")
    monkeypatch.setattr(settings, "S3_BUCKET_NAME", "my-bucket")
    monkeypatch.setattr(settings, "AWS_REGION", "ap-south-1")
    assert storage.image_url("a.png") == "https://my-bucket.s3.ap-south-1.amazonaws.com/a.png"
    monkeypatch.setattr(settings, "IMAGE_BASE_URL", "https://d123.cloudfront.net")
    assert storage.image_url("a.png") == "https://d123.cloudfront.net/a.png"


def test_s3_not_configured_status(monkeypatch):
    from app.config import settings
    from app.services import cloudinfo
    monkeypatch.setattr(settings, "S3_BUCKET_NAME", "")
    assert cloudinfo.s3_status()["state"] == "not_configured"


def test_s3_error_is_handled_not_raised(monkeypatch):
    from app.config import settings
    from app.services import cloudinfo

    class Broken:
        def head_bucket(self, **kw):
            raise RuntimeError("boom")
    monkeypatch.setattr(settings, "S3_BUCKET_NAME", "some-bucket")
    monkeypatch.setattr(cloudinfo, "_s3_client", lambda: Broken())
    cloudinfo._cache.pop("s3", None)
    res = cloudinfo.s3_status()
    cloudinfo._cache.pop("s3", None)
    assert res["state"] == "error" and "RuntimeError" in res["detail"]


# ---------------- Cloud Lab ----------------
def test_cloud_pages_open(client):
    for url in ("/cloud", "/cloud/syllabus", "/cloud/mapreduce", "/cloud/mapreduce?source=sample", "/cloud/unit5"):
        assert client.get(url).status_code == 200, url


def test_cloud_status_has_no_secrets(client):
    from app.config import settings
    r = client.get("/cloud/status")
    assert r.status_code == 200
    body = r.text
    assert r.json()["database"]["connected"] is True
    for secret in (settings.DATABASE_PASSWORD, settings.SECRET_KEY, settings.DATABASE_HOST):
        if secret and secret not in ("localhost",):
            assert secret not in body
    assert "password" not in body.lower()


def _status_of(cards, name):
    return next(c["status"] for c in cards if c["name"] == name)


def test_cloud_cards_are_honest_when_not_on_ec2(monkeypatch):
    from app.services import cloudinfo
    monkeypatch.setattr(cloudinfo, "ec2_info", lambda: {"on_ec2": False})
    cards = cloudinfo.service_cards({})
    assert _status_of(cards, "Amazon EC2") == "Not configured"       # never a fake green status
    assert _status_of(cards, "AWS IAM") == "Not configured"
    assert _status_of(cards, "Elastic Load Balancer") == "Optional"
    assert _status_of(cards, "EC2 Auto Scaling") == "Optional"


def test_cloud_cards_verified_only_with_evidence(monkeypatch):
    from app.services import cloudinfo
    monkeypatch.setattr(cloudinfo, "ec2_info", lambda: {"on_ec2": True, "instance_type": "t3.micro", "az": "ap-south-1a", "iam_role": True})
    cards = cloudinfo.service_cards({"X-Amzn-Trace-Id": "Root=1-abc"})
    assert _status_of(cards, "Amazon EC2") == "Configured and verified"
    assert _status_of(cards, "AWS IAM") == "Configured and verified"
    assert _status_of(cards, "Elastic Load Balancer") == "Configured and verified"
    assert _status_of(cards, "Amazon CloudWatch") == "Configured but not verified"   # cannot be proven from inside


def test_mapreduce_logic():
    from app.services import mapreduce
    res = mapreduce.run(mapreduce.SAMPLE)
    totals = {r["product"]: r["units"] for r in res["reduced"]}
    assert totals == {"Laptop": 10, "Phone": 25, "Headphones": 15, "Watch": 8}
    assert res["reduced"][0]["product"] == "Laptop"            # 10 * 55999 is the largest sales value
