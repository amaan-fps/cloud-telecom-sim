let currentNodeId = null;
let panelInterval = null;

let latencyChart, signalChart;

function openNodePanel(node) {
  currentNodeId = node.node_id;
  document.getElementById("side-panel").classList.add("open");
  document.getElementById("panel-title").innerText = node.node_id;

  startPanelUpdates();
}

function closeNodePanel() {
  document.getElementById("side-panel").classList.remove("open");
  currentNodeId = null;
  if (panelInterval) clearInterval(panelInterval);
}

async function startPanelUpdates() {
  if (panelInterval) clearInterval(panelInterval);

  await updatePanel();
  panelInterval = setInterval(updatePanel, 3000);
}

async function updatePanel() {
  if (!currentNodeId) return;

  const res = await fetch(`/api/nodes/${currentNodeId}/history`);
  const data = await res.json();

  const labels = data.points.map(p => p.timestamp.split("T")[1].slice(0, 8));
  const latency = data.points.map(p => p.latency_ms);
  const signal = data.points.map(p => p.signal_strength);

  renderLatencyChart(labels, latency);
  renderSignalChart(labels, signal);
}

function renderLatencyChart(labels, data) {
  if (latencyChart) latencyChart.destroy();

  latencyChart = new Chart(
    document.getElementById("latencyChart"),
    {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Latency (ms)",
          data,
          borderColor: "#3498db",
          tension: 0.3
        }]
      },
      options: { responsive: true }
    }
  );
}

function renderSignalChart(labels, data) {
  if (signalChart) signalChart.destroy();

  signalChart = new Chart(
    document.getElementById("signalChart"),
    {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Signal Strength",
          data,
          borderColor: "#2ecc71",
          tension: 0.3
        }]
      },
      options: { responsive: true }
    }
  );
}
