#!/bin/bash
# Installs the CloudWatch agent on the EC2 instance and ships the application log.
# Needs the instance role to include the policy "CloudWatchAgentServerPolicy". Run:  bash deploy/cloudwatch_setup.sh
set -e
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ARCH=$(dpkg --print-architecture)   # amd64 or arm64
wget -q "https://amazoncloudwatch-agent.s3.amazonaws.com/ubuntu/${ARCH}/latest/amazon-cloudwatch-agent.deb" -O /tmp/cwagent.deb
sudo dpkg -i /tmp/cwagent.deb
# point the config at the real log path of this server
sed "s|/home/ubuntu/CloudCart|$APP_DIR|g" "$APP_DIR/deploy/cloudwatch-agent-config.json" | sudo tee /opt/aws/amazon-cloudwatch-agent/etc/cloudcart.json >/dev/null
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file:/opt/aws/amazon-cloudwatch-agent/etc/cloudcart.json -s
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a status
echo "Done. In the console open CloudWatch > Logs > Log groups > cloudcart-app-logs"
