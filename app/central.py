# app/central.py
import boto3
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sqlite3
from datetime import datetime, timezone

app = FastAPI()
templates = Jinja2Templates(directory="templates")

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

# ---- Models ----
class Beat(BaseModel):
    node_id: str
    latency_ms: int
    packet_loss: float
    signal_strength: int

class KillRequest(BaseModel):
    node_id: str

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

# Terminate node (requires instance IAM permissions or user credentials on server)
ec2 = boto3.client("ec2", region_name="ap-south-1")

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

# Dashboard page
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})
