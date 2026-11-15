# Architecture

```
User / Browser
      |  HTTP(S)
      v
[CloudFront - optional CDN] --> [Application Load Balancer - optional, health check /health]
      v
EC2 Ubuntu:  Nginx :80 --> Gunicorn + Uvicorn workers :8000 --> FastAPI (Jinja2 pages + JSON API)
      |                                   |
      v                                   v
Amazon RDS MySQL (private)          Amazon S3 (product images, via IAM role)

Supporting: IAM role | VPC + Security Groups | CloudWatch (metrics + logs) | RDS backups | GitHub + deploy scripts
```
**Layers (NIST-style):** presentation (Bootstrap UI), application (FastAPI), data (RDS, S3), infrastructure (EC2, VPC).
**Stateless app:** signed-cookie sessions + RDS + S3 mean any server can serve any request, which allows load balancing and auto scaling.
**Configured vs optional:** EC2, RDS, S3, IAM, security groups and CloudWatch are the basic deployment. CloudFront, ALB and Auto Scaling are optional extensions (docs/OPTIONAL_CLOUDFRONT_ALB_ASG.md).
**Security layers:** security groups (network), IAM role (cloud permissions), password hashing, CSRF tokens, secure headers, parameterized SQL, upload validation, login throttle (application).
