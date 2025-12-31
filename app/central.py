# app/central.py
import boto3
from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Path
from fastapi import Query
from typing import List
from pydantic import BaseModel
import sqlite3
from datetime import datetime, timezone, timedelta
import re
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")
# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---- SQLite setup ----
conn = sqlite3.connect("telecom.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS heartbeats (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  node_id TEXT,
  timestamp TEXT,
  latency_ms INTEGER,
  packet_loss REAL,
  signal_strength INTEGER
)
""")
conn.commit()

ec2 = boto3.client("ec2", region_name="ap-south-1")

# ---------- CONFIG ----------
NODE_REGION = "ap-south-1"
NODE_AMI = "ami-087d1c9a513324697"  # Example: ami-0cca134ec43cf708f
NODE_INSTANCE_TYPE = "t3.micro"
NODE_KEY_NAME = "telecom-project-key"
NODE_SECURITY_GROUP_IDS = "sg-08a95bdc9288da588"  # telecom-sg
NODE_SUBNET_ID = "subnet-0db6f526e79faf876"
NODE_PROJECT_TAG = "CloudTelecomSim"

# ---- Models ----
class Beat(BaseModel):
    node_id: str
    latency_ms: int
    packet_loss: float
    signal_strength: int

class KillRequest(BaseModel):
    node_id: str

class CreateNodesRequest(BaseModel):
    count: int = 1
    name_prefix: str = "base-station"
    instance_type: str = None

# ---- Helper Functions ----
def _get_local_private_ip():
    # Try standard metadata
    try:
        import urllib.request, json
        doc = json.loads(urllib.request.urlopen('http://169.254.169.254/latest/dynamic/instance-identity/document', timeout=2).read().decode())
        return doc.get('privateIp')
    except Exception:
        # fallback to socket
        return socket.gethostbyname(socket.gethostname())

# get existing node list
def fetch_all_node_names_from_ec2():
    """
    Returns a sorted list of existing node numbers.
    Example: ['base-station-1', 'base-station-3'] → [1, 3]
    """
    ec2 = boto3.client("ec2", region_name=NODE_REGION)

    resp = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Project", "Values": ["CloudTelecomSim"]},
            {"Name": "instance-state-name", 
             "Values": ["pending", "running"]}
        ]
    )

    node_numbers = []

    for reservation in resp.get("Reservations", []):
        for inst in reservation.get("Instances", []):
            tags = inst.get("Tags", [])
            for t in tags:
                if t.get("Key") == "Name" and isinstance(t.get("Value"), str):
                    name = t["Value"]
                    # Match pattern base-station-X
                    m = re.match(r"base-station-(\d+)$", name)
                    if m:
                        node_numbers.append(int(m.group(1)))

    return sorted(node_numbers)


# get number for new node based on the existing node count
def get_next_node_number(existing_names):
    """
    existing_names: list of strings like ['base-station-1', 'base-station-3']
    returns the next available node number (gap filling)
    """
    used = []

    # extract all valid numbers
    for num in existing_names:
        try:
            # num = int(name.replace("base-station-", ""))
            used.append(num)
        except ValueError:
            pass

    if not used:
        return 1  # no nodes at all

    used = sorted(used)

    # gap-filling: find the smallest missing positive integer
    expected = 1
    for num in used:
        if num == expected:
            expected += 1
        else:
            # found a gap (e.g., 1,3 → missing 2)
            return expected

    # no gaps found → return next integer
    return expected

# ---- Endpoints ----
@app.post("/heartbeat")
def hb(b: Beat):
    cursor.execute(
        "INSERT INTO heartbeats (node_id, timestamp, latency_ms, packet_loss, signal_strength) VALUES (?, ?, ?, ?, ?)",
        (b.node_id, datetime.utcnow().isoformat(), b.latency_ms, b.packet_loss, b.signal_strength)
    )
    conn.commit()
    print(f"[{b.node_id}] latency={b.latency_ms}ms loss={b.packet_loss} signal={b.signal_strength}")
    return {"ok": True}

@app.get("/latest")
def latest():
    cursor.execute("""
        SELECT node_id, timestamp, latency_ms, packet_loss, signal_strength
        FROM heartbeats
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No heartbeat data yet")
    return {
        "node_id": row[0],
        "timestamp": row[1],
        "latency_ms": row[2],
        "packet_loss": row[3],
        "signal_strength": row[4],
    }

@app.get("/api/nodes")
def get_nodes():
    cursor.execute("""
    SELECT h1.node_id, h1.timestamp, h1.latency_ms, h1.packet_loss, h1.signal_strength
    FROM heartbeats h1
    INNER JOIN (
        SELECT node_id, MAX(timestamp) AS max_ts
        FROM heartbeats
        GROUP BY node_id
    ) h2
    ON h1.node_id = h2.node_id AND h1.timestamp = h2.max_ts
    ORDER BY h1.node_id
    """)
    rows = cursor.fetchall()

    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    nodes = []
    for node_id, ts_str, latency, loss, signal in rows:
        ts = datetime.fromisoformat(ts_str)
        ts = ts.replace(tzinfo=timezone.utc) if ts.tzinfo is None else ts
        age = (now - ts).total_seconds()

        if age < 10:
            status = "online"
        elif age < 30:
            status = "stale"
        else:
            status = "offline"

        nodes.append({
            "node_id": node_id,
            "last_seen": ts_str,
            "age_seconds": age,
            "latency_ms": latency,
            "packet_loss": loss,
            "signal_strength": signal,
            "status": status,
        })

    return {"nodes": nodes}

# get specific node history
@app.get("/api/node/{node_id}/history")
def node_history(
    node_id: str,
    limit: int = Query(50, ge=1, le=500)
):
    """
    Returns recent heartbeat history for a node.
    Used for live charts in side panel.
    """
    cursor.execute("""
        SELECT timestamp, latency_ms, packet_loss, signal_strength
        FROM heartbeats
        WHERE node_id = ?
        ORDER BY id DESC
        LIMIT ?
    """, (node_id, limit))

    rows = cursor.fetchall()
    rows.reverse()  # oldest → newest for charts

    return {
        "node_id": node_id,
        "points": [
            {
                "timestamp": ts,
                "latency_ms": latency,
                "packet_loss": loss,
                "signal_strength": signal
            }
            for ts, latency, loss, signal in rows
        ]
    }

@app.get("/api/summary")
def get_summary():
    cursor.execute("""
        SELECT
            COUNT(*) AS total_nodes,
            SUM(
                CASE
                    WHEN (strftime('%s','now') - strftime('%s', timestamp)) < 10
                    THEN 1 ELSE 0
                END
            ) AS online_nodes,
            ROUND(AVG(latency_ms), 1) AS avg_latency
        FROM (
            SELECT h1.node_id, h1.timestamp, h1.latency_ms
            FROM heartbeats h1
            INNER JOIN (
                SELECT node_id, MAX(timestamp) AS max_ts
                FROM heartbeats
                GROUP BY node_id
            ) h2
            ON h1.node_id = h2.node_id
            AND h1.timestamp = h2.max_ts
        );
    """)

    row = cursor.fetchone()

    total = row[0] or 0
    online = row[1] or 0
    avg_latency = row[2] or 0
    offline = total - online

    return {
        "total_nodes": total,
        "online_nodes": online,
        "offline_nodes": offline,
        "avg_latency": avg_latency,
        # placeholders for later CloudWatch integration
        "cpu_avg": None,
        "memory_avg": None
    }

@app.get("/api/metrics/latency")
def latency_timeseries(limit: int = 50):
    cursor.execute("""
        SELECT timestamp, AVG(latency_ms)
        FROM heartbeats
        GROUP BY timestamp
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()

    rows.reverse()  # oldest → newest

    return {
        "labels": [r[0] for r in rows],
        "values": [round(r[1], 2) for r in rows]
    }

@app.get("/api/metrics/signal")
def signal_strength():
    cursor.execute("""
        SELECT h1.node_id, h1.signal_strength
        FROM heartbeats h1
        INNER JOIN (
            SELECT node_id, MAX(timestamp) AS max_ts
            FROM heartbeats
            GROUP BY node_id
        ) h2
        ON h1.node_id = h2.node_id
        AND h1.timestamp = h2.max_ts
        ORDER BY h1.node_id
    """)
    rows = cursor.fetchall()

    return {
        "nodes": [r[0] for r in rows],
        "signals": [r[1] for r in rows]
    }


# Terminate node (requires instance IAM permissions or user credentials on server)
@app.post("/api/nodes/terminate")
def terminate_node(req: KillRequest):
    resp = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [req.node_id]},
            {"Name": "instance-state-name",
             "Values": ["pending", "running", "stopping", "stopped"]}
        ]
    )

    instance_ids = []
    for reservation in resp["Reservations"]:
        for inst in reservation["Instances"]:
            instance_ids.append(inst["InstanceId"])

    if not instance_ids:
        return {"ok": False, "reason": "No instances found for this node_id"}

    ec2.terminate_instances(InstanceIds=instance_ids)
    return {"ok": True, "terminated": instance_ids}

@app.post("/api/nodes/create")
def create_nodes(req: CreateNodesRequest = Body(...)):
    existing_names = fetch_all_node_names_from_ec2()
    i = get_next_node_number(existing_names)
    name = f"base-station-{i}"
    count = max(1, int(req.count))
    inst_type = req.instance_type or NODE_INSTANCE_TYPE
    collector_ip = _get_local_private_ip()

    # read userdata template file (ensure this file is present in collector repo)
    tpl_path = os.path.join(os.getcwd(), "templates/node_userdata.tpl")
    if not os.path.exists(tpl_path):
        return {"ok": False, "reason": "node_userdata.tpl missing on collector"}

    userdata_tpl = open(tpl_path, "r").read()
    userdata = userdata_tpl.replace("<COLLECTOR_PRIVATE_IP>", collector_ip)
    
    tag_spec = [
        {
            "ResourceType": "instance",
            "Tags": [
                {"Key": "Project", "Value": NODE_PROJECT_TAG},
                {"Key": "Name", "Value": name},
                {"Key": "Role", "Value": "BaseStation"},
            ],
        }
    ]

    # FIXME when creating multiple nodes all at once they get created with same name
    try:
        resp = ec2.run_instances(
            ImageId=NODE_AMI,
            InstanceType=inst_type,
            MinCount=count,
            MaxCount=count,
            KeyName=NODE_KEY_NAME,
            SecurityGroupIds=[NODE_SECURITY_GROUP_IDS],
            SubnetId=NODE_SUBNET_ID,
            IamInstanceProfile={'Name': 'TelecomCollectorProfile'},
            UserData=userdata,
            TagSpecifications=tag_spec,
        )
    except Exception as e:
        return {"ok": False, "error": str(e)}

    instance_ids = [i["InstanceId"] for i in resp.get("Instances", [])]
    return {"ok": True, "launched": instance_ids}

# Dashboard page
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
