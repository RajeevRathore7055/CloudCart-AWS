# Optional: CloudFront, Load Balancer, Auto Scaling

These are **extensions**. The shop works without them. Do not claim they exist unless you created and tested them. The Cloud Lab detects them per request (ALB adds `X-Amzn-Trace-Id`, CloudFront adds `X-Amz-Cf-Id`).

## Why the app is ready for them
Sessions are signed cookies; data is in RDS; uploaded images go to S3; `/health` answers 200/503. So any new server behaves identically. **Requirements:** same `SECRET_KEY` on every server, S3 configured (otherwise images stay on one server), RDS (not a local database).

## A. CloudFront for images (cheap, simple)
CloudFront > Create distribution > origin = your S3 bucket > Origin access = **Origin access control** > create OAC > copy the bucket policy it shows into S3 > default behavior: redirect HTTP to HTTPS > Create. Wait until Deployed. Set `IMAGE_BASE_URL=https://dxxxx.cloudfront.net` in `.env` and restart.

## B. Application Load Balancer
COST WARNING: an ALB is billed hourly. Create, demo, delete.
1. Create `cloudcart-alb-sg`: HTTP 80 from anywhere. Change `cloudcart-ec2-sg` HTTP source to `cloudcart-alb-sg`.
2. EC2 > Target Groups > Create > Instances > HTTP 80 > health check path **/health** > register `cloudcart-web-1`.
3. Load Balancers > Create > Application Load Balancer > internet-facing > at least 2 AZ subnets > `cloudcart-alb-sg` > listener HTTP 80 -> target group.
4. Open the ALB DNS name. Cloud Lab ELB card should become *Configured and verified*.

## C. Auto Scaling
COST WARNING: more instances = more cost. Keep max = 2.
1. EC2 > Instances > select > Actions > Image > **Create image** (AMI) after the app works.
2. Launch Templates > Create from that AMI: `t3.micro`, `cloudcart-ec2-sg`, instance profile `cloudcart-ec2-role`.
3. Auto Scaling Groups > Create > template > 2 subnets > attach the ALB target group > min 1, desired 1, max 2 > **Target tracking: Average CPU 50%** > Create.
4. Demo: `sudo apt install -y stress && stress --cpu 2 --timeout 300` on one instance; watch CloudWatch CPU rise and the group launch a second instance (takes minutes).
5. Delete the Auto Scaling group first, then ALB, target group, AMI + snapshot.
