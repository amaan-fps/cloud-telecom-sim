#!/bin/bash
set -eux

COLLECTOR_IP="<COLLECTOR_PRIVATE_IP>"
REPO_URL="https://github.com/amaan-fps/cloud-telecom-sim.git"
APP_DIR="/home/ubuntu/telecom-node"

apt update -y
apt install -y git python3 python3-venv

sudo -u ubuntu -H bash -lc "
  rm -rf $APP_DIR
  git clone $REPO_URL $APP_DIR
  cd $APP_DIR
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install requests
"

# create systemd unit for node
cat > /etc/systemd/system/base-station.service <<'EOF'
[Unit]
Description=Telecom Base Station Node
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/telecom-node/app
ExecStart=/home/ubuntu/telecom-node/venv/bin/python node.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable base-station
systemctl start base-station
