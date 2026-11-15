# VPC and Security Groups

* **VPC** = your private virtual network. **Subnet** = a slice of it. **Public subnet** has a route to an **Internet Gateway** (IGW); a **private subnet** has no direct route to the internet. **Route table** decides where traffic goes.
* For this project the **default VPC** is used (cost-free, simplest). Its subnets are public, so database privacy comes from: **Public access = No** (no public IP) + a **security group** that only allows the web server.
* A "proper" production layout (explain, do not build unless you have time): EC2 in public subnets behind an ALB, RDS in private subnets, NAT Gateway for outbound access. **NAT Gateway costs money; not used here.**

| Security group | Inbound rule | Why |
|---|---|---|
| `cloudcart-ec2-sg` | HTTP 80 from anywhere; SSH 22 from **My IP only** | Users reach the site; only you administer it |
| `cloudcart-rds-sg` | MySQL 3306 **from `cloudcart-ec2-sg`** | Only the web server can talk to the database |

* Add HTTPS 443 only when you attach a certificate (ACM + CloudFront/ALB).
* Never open 3306 to `0.0.0.0/0`. Security groups are stateful (replies are allowed automatically).
* Safer than SSH: connect through **EC2 Instance Connect** or **Session Manager** (role needs `AmazonSSMManagedInstanceCore`).
