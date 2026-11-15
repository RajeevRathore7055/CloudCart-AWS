# Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `Internal Server Error` | Read the terminal (local) or `sudo journalctl -u cloudcart -n 50` (EC2). Most often a database error |
| `Access denied for user` | `DATABASE_USER` / `DATABASE_PASSWORD` in `.env` wrong |
| `Can't connect to MySQL server` locally | Start MySQL80 in Windows Services |
| Same on EC2 | RDS status not Available, wrong endpoint, or `cloudcart-rds-sg` does not allow `cloudcart-ec2-sg` on 3306 |
| `Unknown database` / missing table | Run `python -m scripts.init_db` |
| `SECRET_KEY missing` | `.env` not in project root |
| 403 "Security check failed" | Page was open too long or cookies blocked. Reload the page and retry |
| Login says too many attempts | 5 wrong passwords lock that e-mail for 15 min (restart the app to clear) |
| 502 Bad Gateway | App not running: `sudo systemctl status cloudcart`, then `journalctl` |
| Site not opening from internet | `cloudcart-ec2-sg` missing HTTP 80, or using https:// with no certificate |
| Images missing after S3 setup | Run the `aws s3 sync` command; check bucket policy / CloudFront; check `S3_BUCKET_NAME`, `AWS_REGION` |
| S3 upload fails | Instance role missing the S3 policy, or role not attached to the instance |
| `$'\r': command not found` | Windows line endings in a `.sh` file. `.gitattributes` prevents it; fix with `sed -i 's/\r$//' deploy/*.sh` |
| `git push` rejected | `git pull --rebase origin main`, then push |
| EC2 Instance Connect fails | Security group must allow SSH (port 22) from the Instance Connect service range, or use Session Manager |
| Cloud Lab shows "Not configured" | Correct when running locally; it only turns green with real evidence |
