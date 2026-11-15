"""Real, non-sensitive facts about the cloud environment this app is running in.
Nothing here is invented: if something cannot be checked it is reported as unverified / not configured.
Never returns passwords, keys, endpoints, bucket names or instance IDs."""
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.db import query_one

START = time.time()
LOG_FILE = Path(__file__).resolve().parent.parent.parent / "logs" / "cloudcart.log"
_cache = {}


def _cached(key, ttl, fn):
    now = time.time()
    hit = _cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1]
    value = fn()
    _cache[key] = (now, value)
    return value


def db_status():
    t = time.perf_counter()
    try:
        query_one("SELECT 1 AS ok")
        is_rds = settings.DATABASE_HOST.endswith(".rds.amazonaws.com")
        return {"ok": True, "latency_ms": round((time.perf_counter() - t) * 1000, 1),
                "engine": "Amazon RDS (MySQL)" if is_rds else "Local / self-managed MySQL", "is_rds": is_rds}
    except Exception:
        return {"ok": False, "latency_ms": None, "engine": "unreachable", "is_rds": False}


def _s3_client():
    import boto3
    from botocore.config import Config
    return boto3.client("s3", region_name=settings.AWS_REGION or None,
                        config=Config(connect_timeout=3, read_timeout=3, retries={"max_attempts": 1}))


def s3_status():
    if not settings.S3_BUCKET_NAME:
        return {"state": "not_configured", "detail": "Images are stored in a local folder on the server."}

    def check():
        try:
            _s3_client().head_bucket(Bucket=settings.S3_BUCKET_NAME)
            return {"state": "verified", "detail": "Bucket is reachable with the credentials available to this server."}
        except Exception as e:
            return {"state": "error", "detail": f"Bucket is configured but not reachable ({type(e).__name__})."}
    return _cached("s3", 60, check)


def ec2_info():
    """Asks the EC2 instance-metadata service (IMDSv2). Only answers if this really runs on EC2."""
    def fetch():
        base = "http://169.254.169.254/latest/"
        try:
            req = urllib.request.Request(base + "api/token", method="PUT",
                                         headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"})
            token = urllib.request.urlopen(req, timeout=0.6).read().decode()

            def get(path):
                r = urllib.request.Request(base + "meta-data/" + path, headers={"X-aws-ec2-metadata-token": token})
                return urllib.request.urlopen(r, timeout=0.6).read().decode()
            info = {"on_ec2": True, "instance_type": get("instance-type"), "az": get("placement/availability-zone")}
            try:
                get("iam/security-credentials/")
                info["iam_role"] = True
            except Exception:
                info["iam_role"] = False
            return info
        except Exception:
            return {"on_ec2": False}
    return _cached("ec2", 300, fetch)


def region():
    if settings.AWS_REGION:
        return settings.AWS_REGION
    info = ec2_info()
    return info["az"][:-1] if info.get("on_ec2") else "Not configured"


def logging_status():
    if LOG_FILE.exists():
        return "Application writes logs to a file. Whether the CloudWatch agent ships them is not verified from inside the app."
    return "No application log file found yet."


def status_json():
    ec2 = ec2_info()
    db = db_status()
    return {
        "application": {"status": "ok", "uptime_seconds": int(time.time() - START), "version": "1.0.0"},
        "database": {"connected": db["ok"], "latency_ms": db["latency_ms"], "engine": db["engine"]},
        "s3": s3_status(),
        "aws_region": region(),
        "cloudwatch": {"state": "unverified", "detail": logging_status()},
        "ec2": {"running_on_ec2": ec2.get("on_ec2", False), "instance_type": ec2.get("instance_type"),
                "availability_zone": ec2.get("az"), "iam_role_attached": ec2.get("iam_role", False)},
        "checked_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
    }


V, CNV, OPT, CON, NC = ("Configured and verified", "Configured but not verified", "Optional",
                         "Conceptual demonstration", "Not configured")


def service_cards(headers):
    """Nine AWS service cards. 'status' is derived from real checks wherever that is possible."""
    ec2, db, s3 = ec2_info(), db_status(), s3_status()
    on = ec2.get("on_ec2", False)
    h = {k.lower(): v for k, v in headers.items()}
    via_alb = "x-amzn-trace-id" in h
    via_cf = "x-amz-cf-id" in h or "cloudfront" in h.get("via", "").lower()
    cf_cfg = "cloudfront.net" in settings.IMAGE_BASE_URL

    def card(name, icon, purpose, usage, status, note):
        return {"name": name, "icon": icon, "purpose": purpose, "usage": usage, "status": status, "note": note}

    return [
        card("Amazon EC2", "bi-hdd-network", "Virtual servers rented on demand (IaaS).",
             "Runs Nginx + Gunicorn + the FastAPI app.",
             V if on else NC, f"Verified through instance metadata ({ec2.get('instance_type')}, {ec2.get('az')})." if on else "This copy is not running on EC2 (local run)."),
        card("Amazon RDS", "bi-database", "Managed relational database with automated backups.",
             "Stores users, products, carts and orders (MySQL).",
             V if (db["ok"] and db["is_rds"]) else NC, "Connected to an RDS endpoint." if db["is_rds"] and db["ok"] else "Using local MySQL. Point DATABASE_HOST to RDS to enable."),
        card("Amazon S3", "bi-bucket", "Durable object storage (Storage-as-a-Service).",
             "Holds product images uploaded by the admin.",
             {"verified": V, "error": CNV}.get(s3["state"], NC), s3["detail"]),
        card("AWS IAM", "bi-shield-lock", "Identity and access management.",
             "EC2 instance role gives S3 access without storing keys in code.",
             V if ec2.get("iam_role") else NC, "An instance role is attached to this server." if ec2.get("iam_role") else "No instance role detected."),
        card("Amazon VPC + Security Groups", "bi-diagram-2", "Isolated virtual network and instance firewall.",
             "EC2 allows HTTP/SSH; the database only accepts traffic from the web server's group.",
             CNV if on else CON, "Server runs inside a VPC. Rules cannot be inspected from inside the app." if on else "Explained in docs; nothing to verify locally."),
        card("Amazon CloudWatch", "bi-activity", "Metrics, logs and alarms.",
             "CPU/network metrics of EC2 and the application log file.",
             CNV if on else NC, "Agent shipping is not verified from inside the app."),
        card("Amazon CloudFront", "bi-globe2", "Global CDN that caches content near users.",
             "Optional: serves S3 product images faster.",
             V if via_cf else (CNV if cf_cfg else OPT), "This request arrived through CloudFront." if via_cf else ("Image base URL points to CloudFront." if cf_cfg else "Not part of the basic deployment.")),
        card("Elastic Load Balancer", "bi-signpost-split", "Spreads traffic across healthy servers.",
             "Optional: ALB would use the /health endpoint.",
             V if via_alb else OPT, "This request arrived through an AWS load balancer." if via_alb else "Not part of the basic deployment."),
        card("EC2 Auto Scaling", "bi-arrows-angle-expand", "Adds or removes servers automatically (elasticity).",
             "Optional: needs S3 images and RDS so servers stay stateless.",
             OPT, "Application is designed to be stateless, but no scaling group is verified."),
    ]
