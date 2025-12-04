# app/node.py
import time
import os
import requests
import socket
import boto3

OLLECTOR = os.environ.get("COLLECTOR_URL")  # prefer env var if setC
if not COLLECTOR:
    # fallback: check /etc or a file
    COLLECTOR = "http://<COLLECTOR_PRIVATE_IP>:5000"  # replaced by userdata template

session = requests.Session()

# Attempt to get a node id from EC2 metadata tags (if on EC2 with IAM)
node_id = None
try:
    # if running on EC2, try to fetch tag 'Name'
    from botocore import exceptions
    ec2 = boto3.client('ec2', region_name='ap-south-1')
    # metadata fetch
    import urllib.request, json
    doc = json.loads(urllib.request.urlopen('http://169.254.169.254/latest/dynamic/instance-identity/document', timeout=2).read().decode())
    instance_id = doc.get('instanceId')
    if instance_id:
        resp = ec2.describe_instances(InstanceIds=[instance_id])
        tags = resp['Reservations'][0]['Instances'][0].get('Tags', [])
        for t in tags:
            if t.get('Key') == 'Name':
                node_id = t.get('Value')
                break
except Exception:
    pass

if not node_id:
    node_id = socket.gethostname()

print("Using node id:", node_id)
url = COLLECTOR.rstrip('/') + '/heartbeat'

import random
while True:
    payload = {
        "node_id": node_id,
        "latency_ms": random.randint(10, 300),
        "packet_loss": round(random.random()*5, 2),
        "signal_strength": random.randint(10, 100)
    }
    try:
        r = session.post(url, json=payload, timeout=5)
        if r.ok:
            print("Sent:", payload)
        else:
            print("POST failed:", r.status_code, r.text)
    except Exception as e:
        print("Error sending heartbeat:", e)
    time.sleep(3)
