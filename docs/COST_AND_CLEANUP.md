# Cost control and cleanup

Eligibility and pricing change; always verify in *Billing and Cost Management*. Set a budget alert before creating anything.

| Resource | Cost risk | After the demo |
|---|---|---|
| EC2 t3.micro | hours running + public IPv4 address | **Terminate** (Stop still keeps EBS volume charges) |
| EBS volume | storage | deleted with the instance (default) |
| RDS db.t3.micro | hours + storage + backups | take a final snapshot if needed, then **Delete** (untick "retain automated backups" if you want zero cost) |
| S3 bucket | small storage | empty bucket, then delete |
| CloudFront / ALB / ASG | ALB is hourly | delete ASG, ALB, target group, distribution (disable first) |
| NAT Gateway | **expensive** | never created in this project |
| CloudWatch logs | ingestion + storage | delete log group |

Order of deletion: Auto Scaling group > Load balancer > Target group > EC2 > RDS > S3 > CloudFront > security groups > IAM role. Finally check *Billing > Bills* the next day.
