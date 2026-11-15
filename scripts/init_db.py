"""Create database, tables, sample data and admin/demo users.

Usage:   python -m scripts.init_db            (safe: skips if tables already exist)
         python -m scripts.init_db --reset    (DROPS the database and rebuilds it)
Works for local MySQL and for AWS RDS (just change .env).
"""
import os
import secrets
import sys
from pathlib import Path

import pymysql
from werkzeug.security import generate_password_hash

from app.config import settings

ROOT = Path(__file__).resolve().parent.parent


def run_sql_file(cur, path):
    for stmt in path.read_text(encoding="utf-8").split(";"):
        if stmt.strip():
            cur.execute(stmt)


def main():
    reset = "--reset" in sys.argv
    db = settings.DATABASE_NAME.replace("`", "")
    conn = pymysql.connect(
        host=settings.DATABASE_HOST, port=settings.DATABASE_PORT,
        user=settings.DATABASE_USER, password=settings.DATABASE_PASSWORD,
        charset="utf8mb4", autocommit=True,
    )
    with conn.cursor() as cur:
        if reset:
            cur.execute(f"DROP DATABASE IF EXISTS `{db}`")
            print(f"Dropped database {db}")
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db}` CHARACTER SET utf8mb4")
        cur.execute(f"USE `{db}`")
        cur.execute("SHOW TABLES LIKE 'users'")
        if cur.fetchone():
            print("Tables already exist - skipping schema/sample data (use --reset to rebuild).")
        else:
            run_sql_file(cur, ROOT / "database" / "schema.sql")
            run_sql_file(cur, ROOT / "database" / "sample_data.sql")
            print("Schema and sample data loaded.")

        admin_pwd = os.getenv("ADMIN_PASSWORD")
        if not admin_pwd:
            admin_pwd = secrets.token_urlsafe(12)
            print(f"ADMIN_PASSWORD not set -> generated one-time admin password: {admin_pwd}  (save it now)")
        elif admin_pwd == "Admin@123" and settings.DATABASE_HOST not in ("localhost", "127.0.0.1"):
            print("WARNING: default demo admin password in use on a remote database. Set a strong ADMIN_PASSWORD in .env!")
        users = [
            ("Admin", os.getenv("ADMIN_EMAIL", "admin@cloudcart.com"), admin_pwd, "admin"),
            ("Demo Customer", "demo@cloudcart.com", "Customer@123", "customer"),
        ]
        for name, email, pwd, role in users:
            cur.execute("SELECT id FROM users WHERE email=%s", (email,))
            if cur.fetchone():
                print(f"User exists: {email}")
                continue
            cur.execute("INSERT INTO users (name,email,password_hash,role) VALUES (%s,%s,%s,%s)",
                        (name, email, generate_password_hash(pwd), role))
            print(f"Created {role}: {email}")
    conn.close()
    print("Database ready.")


if __name__ == "__main__":
    main()
