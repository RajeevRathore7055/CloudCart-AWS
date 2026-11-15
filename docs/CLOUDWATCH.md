# CloudWatch: monitoring and logs

**Metrics (automatic):** EC2 > Instances > select > **Monitoring** tab shows CPUUtilization, Network in/out, Status checks (basic monitoring, 5-minute data, free).

**Application logs (agent):**
1. Instance role must include `CloudWatchAgentServerPolicy` (see IAM_POLICY.md).
2. On the server: `bash deploy/cloudwatch_setup.sh`.
3. Console > CloudWatch > Logs > Log groups > `cloudcart-app-logs` > open the stream. Each request is logged like `GET /products -> 200 (8 ms)`.

**Demo script for faculty**
1. Open the site and click around; show CPU graph (it moves slowly; data is 5-minute).
2. Show log group; search `-> 500` or `ERROR` to find errors; open a failing request to explain investigation.
3. Optional alarm: CloudWatch > Alarms > Create > metric `CPUUtilization` > threshold 70% > email via SNS.

**Honesty:** the Cloud Lab page marks CloudWatch "Configured but not verified" because the app cannot prove the agent is shipping logs. Verify in the console.
