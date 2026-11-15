# AWS Deployment Guide (step by step)

Use **one region** for everything (this guide assumes `ap-south-1`, Mumbai). Check the region name at the top-right of the console before every step. Do not use the root account for daily work: sign in as an IAM user.

> **Cost safety.** Free Tier / free-plan eligibility and prices depend on your account type and region, so check *Billing > Free tier* yourself. Use only `t3.micro`, `db.t3.micro`, 20 GB storage, **no Multi-AZ, no NAT Gateway**. Create a budget alert first. Delete everything after the demo (see COST_AND_CLEANUP.md). Never click "Upgrade plan" by accident.

## 0. Prerequisites
* Code pushed to GitHub (`git push -u origin main`). `.env` must NOT be in the repo.
* AWS account active, MFA on root, an IAM user (e.g. `cloudcart-admin`) used for sign-in.
* Billing > Budgets > Create budget > Monthly cost budget, e.g. USD 5, your e-mail.

## 1. Security groups (EC2 > Network & Security > Security Groups)
Create `cloudcart-ec2-sg` (SSH from My IP, HTTP from Anywhere-IPv4) **first**, then `cloudcart-rds-sg` (MYSQL/Aurora 3306, source = `cloudcart-ec2-sg`). Details: VPC_SECURITY.md.

## 2. RDS MySQL (start early: takes 5-10 minutes)
RDS > Create database > Standard create > MySQL > template **Free tier** (or Dev/Test, Single-AZ) > identifier `cloudcart-db` > master user `admin` + strong password (letters/numbers only, save it) > `db.t3.micro` > storage gp3/General Purpose 20 GiB, **disable storage autoscaling** > connectivity: Default VPC, **Public access = No**, security group `cloudcart-rds-sg` > Additional configuration: initial database name `cloudcart`, **backup retention 7 days**, deletion protection off > Create.
Copy the **Endpoint** when status = Available.
**Backups:** automated backups are enabled by the retention setting. Manual snapshot: RDS > Databases > Actions > Take snapshot.

## 3. IAM role (see IAM_POLICY.md) and S3 (see S3_SETUP.md)
Create the role first so you can attach it while launching EC2. Create the bucket now or later.

## 4. Launch EC2
EC2 > Launch instance: name `cloudcart-web-1`, **Ubuntu Server 24.04 LTS**, `t3.micro`, new key pair `cloudcart-key` (.pem, keep private, never commit), network: default VPC, **auto-assign public IP = enable**, existing security group `cloudcart-ec2-sg`, storage 12 GiB gp3, Advanced details > **IAM instance profile** = `cloudcart-ec2-role`. Launch, wait for 2/2 status checks, copy the public IPv4 address.

## 5. Connect
Console > select instance > **Connect** > *EC2 Instance Connect* > Connect (browser terminal, no .pem needed).

## 6. Deploy from GitHub
```bash
git clone https://github.com/<your-username>/CloudCart.git
cd CloudCart
cp .env.example .env
nano .env        # Ctrl+O, Enter, Ctrl+X to save
```
Fill `.env` (use quotes if a value has special characters):
```
DATABASE_HOST=<RDS endpoint>
DATABASE_USER=admin
DATABASE_PASSWORD=<rds password>
DATABASE_NAME=cloudcart
SECRET_KEY=<output of: python3 -c "import secrets; print(secrets.token_hex(32))">
ADMIN_PASSWORD=<a strong password you choose>
AWS_REGION=ap-south-1
S3_BUCKET_NAME=<bucket, after S3 step>
```
Then:
```bash
bash deploy/ec2_setup.sh
```
It installs packages, builds the virtualenv, creates tables + sample data on RDS (`init_db` never deletes existing data), creates the `cloudcart` systemd service and Nginx. Open `http://<public-ip>/` and `http://<public-ip>/health` (expect `{"status":"ok","database":"up"}`).

To test the database link by hand (mysql-client is installed by the script): `mysql -h <endpoint> -u admin -p -e "SHOW DATABASES;"`.

## 7. S3 images and CloudWatch
S3_SETUP.md, then `sudo systemctl restart cloudcart`. CloudWatch: `bash deploy/cloudwatch_setup.sh` (CLOUDWATCH.md).

## 8. Update the site after code changes
Push to GitHub, then on EC2: `bash deploy/update.sh`.

## 9. Check the Cloud Lab
Open `http://<public-ip>/cloud`. EC2, RDS, S3, IAM should now show *Configured and verified* (only when really true). VPC and CloudWatch stay *Configured but not verified* by design.

## 10. HTTPS (optional)
HTTPS needs a domain + certificate (ACM) on CloudFront or an ALB. After that set `COOKIE_SECURE=true` and restart.

## Disaster recovery (procedure; test it before claiming it works)
1. RDS > Snapshots > select snapshot > **Restore snapshot** (creates a *new* instance with a new endpoint).
2. Put the new endpoint in `.env` (`DATABASE_HOST`), `sudo systemctl restart cloudcart`.
3. Lost server? Launch a new EC2 with the same role/security group, clone from GitHub, same `.env`, run `ec2_setup.sh`.
4. Images in S3 are unaffected.
