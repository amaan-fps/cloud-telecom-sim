#!/bin/bash
set -eux

# --- Variables (edit repo URL) ---
REPO_URL="https://github.com/amaan-fps/cloud-telecom-sim.git"
APP_DIR="/home/ubuntu/telecom-central"

# --- Basic deps ---
apt update -y
apt install -y git python3 python3-pip python3-venv

# --- Clone the app as ubuntu user ---
sudo -u ubuntu -H bash -lc "
  rm -rf $APP_DIR
  git clone $REPO_URL $APP_DIR
  cd $APP_DIR
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt || pip install fastapi 'uvicorn[standard]' boto3 sqlite-utils jinja2
"

# --- Create systemd unit ---
cat > /etc/systemd/system/collector.service <<'EOF'
[Unit]
Description=Telecom Collector API
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/telecom-central/app
ExecStart=/home/ubuntu/telecom-central/venv/bin/uvicorn central:app --host 0.0.0.0 --port 5000
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable collector
systemctl start collector
