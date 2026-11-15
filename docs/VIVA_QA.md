# Viva questions and simple answers

**What is cloud computing?** Using computing resources (servers, storage, databases) over the internet on demand and paying for what you use, instead of owning hardware.
**Why AWS?** Largest provider, free-tier/learning options, every service we need (EC2, RDS, S3, IAM, CloudWatch).
**EC2?** Virtual servers (IaaS). Our FastAPI app runs on one.
**S3?** Object storage. We keep product images there so they survive server loss and any server can show them.
**RDS?** Managed MySQL: AWS handles patching and backups. We only use the database.
**Why RDS instead of local MySQL?** Backups, snapshots, separate from the web server (so servers can be replaced or multiplied), restore without reinstalling.
**IAM?** Controls who can do what. The EC2 instance has a role allowing only our S3 bucket (least privilege); no keys in code.
**VPC?** Our private virtual network. **Security group:** instance firewall; RDS accepts MySQL only from the web server's group.
**CloudWatch?** Metrics (CPU) and logs. We ship the application log and watch CPU.
**CloudFront?** CDN that caches content near users (optional for images).
**Load balancing?** Spreads requests over several servers and uses `/health` to skip a sick one (optional).
**Auto Scaling?** Adds/removes servers by rule, e.g. CPU above 50% (optional).
**How does a request reach the backend?** Browser > (CloudFront) > (ALB) > Nginx on EC2 > Gunicorn/FastAPI > RDS/S3 > response.
**Traffic increases?** With ALB + ASG, new instances start (needs stateless app: RDS + S3 + shared secret key). Without them, upgrade the instance size.
**EC2 instance fails?** Single server: the site is down until we launch a new one from GitHub (data is safe in RDS/S3). With ALB + ASG the group replaces it automatically.
**Scalability / elasticity / availability?** Scalability: can handle more load by adding resources. Elasticity: does it automatically, up and down. Availability: stays reachable when parts fail (multiple servers, Multi-AZ).
**IaaS vs PaaS vs SaaS?** IaaS: you get a virtual server (EC2). PaaS: you give code, platform runs it (App Engine, Elastic Beanstalk). SaaS: finished software over the internet (CloudCart for shoppers).
**What is virtualization?** One physical machine split into isolated virtual machines by a hypervisor.
**How is CloudCart secured?** Hashed passwords, CSRF tokens, security headers, parameterized SQL (no SQL injection), admin checks, upload validation, login throttling, IAM role, security groups, secrets only in environment variables.
**What is MapReduce?** Map turns data into key/value pairs, shuffle groups by key, reduce combines each group. We simulate it for product sales.
**What did you NOT implement?** Be honest: ALB, CloudFront, Auto Scaling, HTTPS and DR restore tests are optional or untested unless you actually did them.
