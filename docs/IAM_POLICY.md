# IAM: least-privilege role for the EC2 server

**Never use the root account for the app and never put access keys in code or in `.env`.**
The EC2 instance gets a *role*; Boto3 finds temporary credentials automatically.

## 1. Role for EC2
IAM > Roles > Create role > AWS service > **EC2** > attach `CloudWatchAgentServerPolicy` > name `cloudcart-ec2-role`.

## 2. Inline policy: only this bucket, only needed actions
Role > Add permissions > Create inline policy > JSON. Replace `YOUR-BUCKET-NAME`.
```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*" },
    { "Effect": "Allow", "Action": ["s3:ListBucket"], "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME" }
  ]
}
```
`ListBucket` also lets the Cloud Lab "S3 status" check (`head_bucket`) succeed.

## 3. Attach to the instance
EC2 > Instances > select > Actions > Security > **Modify IAM role** > `cloudcart-ec2-role`.

## 4. Verify (on the server)
`aws sts get-caller-identity` shows the role (install CLI: `sudo snap install aws-cli --classic`). Cloud Lab shows IAM as *Configured and verified* only when the role is really attached.

## Viva points
Least privilege = only the actions and resources required. Roles give temporary credentials, so there is no secret to leak.
