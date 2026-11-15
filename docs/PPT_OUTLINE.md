# Presentation outline (12-15 slides)

1. Title: CloudCart, Cloud-Based E-Commerce Platform (name, roll no., guide)
2. Problem statement: businesses need scalable, always-available stores without owning servers
3. Objectives: apply cloud concepts (virtualization, storage, managed DB, security, monitoring) in a real app
4. Proposed solution: FastAPI shop + AWS deployment
5. Technology stack: FastAPI, MySQL, Bootstrap, Boto3, Nginx/Gunicorn, GitHub Actions
6. Cloud architecture diagram (docs/ARCHITECTURE.md or Cloud Lab section 1)
7. AWS services: EC2, RDS, S3, IAM, VPC/SG, CloudWatch (+ optional CloudFront, ALB, ASG) with honest status
8. Service models: IaaS / PaaS / SaaS and where CloudCart fits
9. Virtualization and elasticity
10. Security: layers (network, IAM, application)
11. Screenshots: shop, admin dashboard, Cloud Lab
12. Live demo flow (below)
13. Disaster recovery and cost control
14. Challenges and learning; Unit V concepts (MapReduce demo)
15. Future scope and conclusion

## Live demo flow
Home > register/login > search/filter > add to cart > checkout > order history > admin login > add product (upload image) > update order status > Cloud Lab (architecture, status, MapReduce) > AWS console: EC2, RDS, S3, IAM role, security groups, CloudWatch graph/logs > explain optional ALB/ASG honestly.
