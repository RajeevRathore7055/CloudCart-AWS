# Cloud Computing syllabus mapping

Also available live in the app at `/cloud/syllabus`. **Implemented** = real in code or deployment; **Simulated** = small working demo; **Conceptual** = explained only.

| Unit | Concept | CloudCart example | Status |
|---|---|---|---|
| I | Definition, characteristics, on-demand provisioning | App rented as services (EC2/RDS/S3), launched in minutes | Implemented when deployed |
| I | Elasticity, parallel/distributed computing | Gunicorn workers; ALB + Auto Scaling (optional) | Optional / conceptual |
| II | SOA, web services, REST | `/api/products`, `/health`, `/cloud/status`, Swagger `/docs` | Implemented |
| II | Publish/subscribe | Would be SNS/SQS for order e-mails | Conceptual |
| II | Virtualization (CPU/memory/I-O) | EC2 instance = VM on a hypervisor | Conceptual (EC2 is real) |
| II | Disaster recovery | RDS backups/snapshots, GitHub redeploy, S3 images | Configuration; restore not tested |
| III | Layered / NIST architecture | UI, FastAPI, RDS/S3 layers | Conceptual |
| III | Public/private/hybrid cloud | AWS public cloud; OpenStack = private | Conceptual |
| III | IaaS/PaaS/SaaS | EC2 (IaaS), RDS (managed), CloudCart (SaaS) | Explained |
| III | Cloud storage, S3 | Product images via Boto3 | Implemented (needs S3 setup) |
| IV | Resource provisioning | Console steps + `ec2_setup.sh` | Implemented |
| IV | Security, SaaS security, IAM | Hashing, CSRF, headers, IAM role, security groups | Implemented |
| IV | Inter-cloud management | Not applicable to single-cloud app | Conceptual |
| V | MapReduce | `/cloud/mapreduce` computes sales per product | Simulated (no Hadoop) |
| V | VirtualBox, App Engine, OpenStack, federation | `/cloud/unit5` | Conceptual |
