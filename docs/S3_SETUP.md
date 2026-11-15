# S3 for product images

1. S3 > Create bucket: name `cloudcart-images-<your-name>-<random>` (globally unique), region = your project region.
2. Keep **Block all public access ON** (recommended). Do not add ACLs.
3. Choose how images are shown:
   * **Option A (recommended): CloudFront.** Create a distribution with the bucket as origin and **Origin Access Control**; apply the bucket policy CloudFront suggests. Set `IMAGE_BASE_URL=https://dxxxx.cloudfront.net` in `.env`.
   * **Option B (quick demo only): public read.** Turn Block public access off for this bucket and add:
```json
{ "Version": "2012-10-17", "Statement": [ { "Effect": "Allow", "Principal": "*",
  "Action": "s3:GetObject", "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*" } ] }
```
     Anyone can read the images (they are product photos). Delete the bucket after the demo.
4. `.env` on the server: `AWS_REGION=<region>` and `S3_BUCKET_NAME=<bucket>`. No keys.
5. Upload the demo images once (from your laptop with AWS CLI configured, or CloudShell):
   `aws s3 sync app/static/images s3://YOUR-BUCKET-NAME/ --exclude "uploads/*"`
6. Restart: `sudo systemctl restart cloudcart`. Admin > Add product > upload: the file appears in the bucket.

Notes: uploads are validated (JPG/PNG/WEBP/GIF, max 2 MB). Deleting a product deletes only admin-uploaded files, never the bundled demo images.
