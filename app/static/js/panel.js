let panelNodeId = null;
let panelInterval = null;
let latencyChart = null;
let signalChart = null;

function openNodePanel(node) {
  panelNodeId = node.node_id;

  document.getElementById("panel-title").innerText = node.node_id;
  document.getElementById("side-panel").classList.add("open");

  initCharts();
  updatePanelData();

  // Refresh every 2 seconds
  panelInterval = setInterval(updatePanelData, 2000);
}

function closeNodePanel() {
  panelNodeId = null;
  document.getElementById("side-panel").classList.remove("open");

  if (panelInterval) {
    clearInterval(panelInterval);
    panelInterval = null;
  }
}

async function updatePanelData() {
  if (!panelNodeId) return;

  try {
    // Fetch latest snapshot
    const res = await fetch("/api/nodes");
    const data = await res.json();
    const node = data.nodes.find(n => n.node_id === panelNodeId);
    if (!node) return;

    document.getElementById("panel-status").innerText = node.status;
    document.getElementById("panel-status").className = "panel-status " + node.status;

    document.getElementById("panel-latency").innerText = node.latency_ms;
    document.getElementById("panel-loss").innerText = node.packet_loss;
    document.getElementById("panel-signal").innerText = node.signal_strength;
    document.getElementById("panel-last-seen").innerText = node.last_seen;

    // Fetch history for charts
    const hRes = await fetch(`/api/node/${panelNodeId}/history?limit=30`);
    const history = await hRes.json();

    updateCharts(history.points);

  } catch (err) {
    console.error("Panel update failed:", err);
  }
}

function initCharts() {
  const latencyCtx = document.getElementById("latencyChart").getContext("2d");
  const signalCtx = document.getElementById("signalChart").getContext("2d");

  if (latencyChart) latencyChart.destroy();
  if (signalChart) signalChart.destroy();

  latencyChart = new Chart(latencyCtx, {
    type: "line",
    data: { labels: [], datasets: [{
      label: "Latency (ms)",
      data: [],
      borderColor: "#3498db",
      tension: 0.3
    }]},
    options: { responsive: true, animation: false }
  });

  signalChart = new Chart(signalCtx, {
    type: "line",
    data: { labels: [], datasets: [{
      label: "Signal Strength",
      data: [],
      borderColor: "#2ecc71",
      tension: 0.3
    }]},
    options: { responsive: true, animation: false }
  });
}

function updateCharts(points) {
  const labels = points.map(p => p.timestamp.slice(11, 19));

  latencyChart.data.labels = labels;
  latencyChart.data.datasets[0].data = points.map(p => p.latency_ms);
  latencyChart.update();

  signalChart.data.labels = labels;
  signalChart.data.datasets[0].data = points.map(p => p.signal_strength);
  signalChart.update();
}
