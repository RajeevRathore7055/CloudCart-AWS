# CloudCart: Cloud-Based E-Commerce Platform

A B.Tech Cloud Computing project: a complete online shop (FastAPI + MySQL) built so that cloud concepts are demonstrated by the real application, not just named. It runs locally with no AWS account, and deploys to AWS (EC2, RDS, S3, IAM, VPC/Security Groups, CloudWatch; optional CloudFront, ALB, Auto Scaling).

## 1. Features
**Customer:** register/login/logout, product catalogue, details, search, category filter, price sort, cart (add/remove/quantity), checkout with *simulated* payment, order confirmation, history, status tracking.
**Admin:** dashboard (users, products, orders, sales, top products), add/edit/delete products with image upload, users list, orders list and status update.
**Cloud Lab (`/cloud`):** architecture, AWS service cards with *honest, evidence-based* status, live health/monitoring, IaaS/PaaS/SaaS, virtualization, REST demo, disaster recovery, syllabus mapping, MapReduce simulation, Unit V explainers.
**REST API:** `GET /api/products`, `/api/products/{id}`, `/health`, `/cloud/status`, Swagger UI at `/docs`.

## 2. Technology
Python 3.12, FastAPI, Jinja2, Bootstrap 5, vanilla JS, MySQL 8 (PyMySQL, parameterized SQL), Boto3, Gunicorn + Uvicorn, Nginx, Git/GitHub, GitHub Actions, Pytest.

## 3. Project structure
```
app/main.py            application, middleware (security headers, access log), /health
app/config.py          environment variables (.env locally, real env vars on AWS)
app/db.py              MySQL connection helpers
app/security.py        auth guards, flash messages, CSRF protection
app/routes/            auth, shop, cart, orders, admin, api, cloud
app/services/          storage.py (local or S3), cloudinfo.py (real cloud status), mapreduce.py
app/templates, static  UI (futuristic dark theme)
database/              schema.sql, sample_data.sql
scripts/               init_db.py (safe, repeatable), make_images.py
deploy/                ec2_setup.sh, update.sh, cloudwatch_setup.sh, cloudwatch-agent-config.json
docs/                  AWS guide, IAM, S3, VPC, CloudWatch, optional services, cost, troubleshooting, viva, PPT
tests/                 33 automated tests
```

## 4. Run locally
See [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md). Short version (PowerShell):
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # edit DB user/password and SECRET_KEY
python -m scripts.init_db
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000. No AWS is needed: leave `AWS_REGION` and `S3_BUCKET_NAME` empty.

## 5. Database
Tables: users, categories, products, cart_items, orders, order_items (foreign keys, unique cart rows, order lines store a price/name snapshot). `init_db` creates the database and loads sample data only when the tables do not exist; it never deletes data unless you pass `--reset`. Same code works for local MySQL and RDS: only `.env` changes.

## 6. Environment variables
`DATABASE_HOST, DATABASE_PORT, DATABASE_NAME, DATABASE_USER, DATABASE_PASSWORD, SECRET_KEY, ADMIN_EMAIL, ADMIN_PASSWORD, COOKIE_SECURE, AWS_REGION, S3_BUCKET_NAME, IMAGE_BASE_URL`. Never commit `.env`. AWS keys are never used: the EC2 IAM role provides credentials.

## 7. AWS deployment
Follow [docs/AWS_DEPLOYMENT.md](docs/AWS_DEPLOYMENT.md). Related: [IAM](docs/IAM_POLICY.md), [S3](docs/S3_SETUP.md), [VPC and security groups](docs/VPC_SECURITY.md), [CloudWatch](docs/CLOUDWATCH.md), [optional CloudFront/ALB/ASG](docs/OPTIONAL_CLOUDFRONT_ALB_ASG.md), [cost and cleanup](docs/COST_AND_CLEANUP.md), [troubleshooting](docs/TROUBLESHOOTING.md).

## 8. What is real and what is optional
| Basic deployment (build and verify) | Optional extensions (only claim if you created them) |
|---|---|
| EC2, RDS, S3, IAM role, Security Groups, CloudWatch, RDS backups, GitHub deploy scripts | CloudFront, Application Load Balancer, Auto Scaling, HTTPS |
The Cloud Lab labels every service from actual checks (database ping, S3 head-bucket, EC2 instance metadata, request headers). Without evidence it shows *Not configured*, *Optional* or *Configured but not verified*, never a fake green status.

## 9. Security
Password hashing (Werkzeug), parameterized SQL, signed session cookies (HttpOnly, SameSite=Lax, Secure when HTTPS), **CSRF tokens on every POST**, security headers (nosniff, frame-ancestors none, referrer policy, HSTS over HTTPS), admin authorization, safe redirects, image upload validation, login throttling (5 failures = 15 min lock; in-memory, per server), secrets only in environment variables, `.env` git-ignored, least-privilege IAM, database reachable only from the web server's security group, `GET /logout` cannot log you out (POST only).
Known limits: login throttle is per process (use a shared store when scaling); `/docs` is public by design for the REST demo.

## 10. Testing
`pytest -v` runs 33 tests: registration, login, invalid login, throttle, CSRF, headers, search/filter, API, cart, stock limits, checkout, order creation + stock update, admin access control, product add/edit/delete, image upload and validation, order status, S3 URL building and error handling, Cloud Lab pages, no secrets in `/cloud/status`, honest status logic, MapReduce. Needs MySQL running and `init_db` done. CI runs them on every push (`.github/workflows/ci.yml`).

## 11. Docs for the presentation
[Syllabus mapping](docs/SYLLABUS_MAPPING.md), [viva Q&A](docs/VIVA_QA.md), [PPT outline](docs/PPT_OUTLINE.md), [architecture](docs/ARCHITECTURE.md).

## 12. Future improvements
HTTPS with ACM, SNS/SQS order notifications, Redis/ElastiCache for shared throttling and sessions, Multi-AZ RDS, Docker/ECS, CodePipeline, real payment gateway.
"# CloudCart-AWS" 
