# Local setup (Windows PowerShell)

1. Install Python 3.12 (tick "Add to PATH"), MySQL 8 (+ Workbench), Git.
2. ```powershell
   cd CloudCart
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   copy .env.example .env
   notepad .env
   ```
3. In `.env` set `DATABASE_USER`, `DATABASE_PASSWORD` (your MySQL user; `root` is fine locally) and a `SECRET_KEY` (`python -c "import secrets; print(secrets.token_hex(32))"`). Leave the AWS lines empty.
4. ```powershell
   python -m scripts.init_db          # creates database, tables, sample data, admin + demo users
   uvicorn app.main:app --reload      # open http://127.0.0.1:8000
   pytest -v                          # run tests
   ```
Logins: admin `admin@cloudcart.com` / value of `ADMIN_PASSWORD`; customer `demo@cloudcart.com` / `Customer@123`.
Rebuild the database from scratch (**deletes data**): `python -m scripts.init_db --reset`.
Bootstrap and icons load from a CDN, so keep internet on. Images are served from `app/static/images` when S3 is not configured.
