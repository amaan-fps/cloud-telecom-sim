let latencyChart = null;
let signalChart = null;

async function openPanel(node) {
  document.getElementById("panel-node-id").innerText = node.node_id;
  document.getElementById("panel-status").innerText = node.status;
  document.getElementById("panel-latency").innerText = node.latency_ms;
  document.getElementById("panel-loss").innerText = node.packet_loss;
  document.getElementById("panel-signal").innerText = node.signal_strength;
  document.getElementById("panel-last-seen").innerText = node.last_seen;

  document.getElementById("node-panel").classList.remove("hidden");
  document.getElementById("node-panel").classList.add("visible");

  const resp = await fetch(`/api/nodes/${node.node_id}/history`);
  const data = await resp.json();

  renderCharts(data.history);
}

function closePanel() {
  document.getElementById("node-panel").classList.remove("visible");
  document.getElementById("node-panel").classList.add("hidden");
}

function renderCharts(history) {
  const labels = history.map(h => h.ts.split("T")[1].slice(0, 8));
  const latency = history.map(h => h.latency);
  const signal = history.map(h => h.signal);

  if (latencyChart) latencyChart.destroy();
  if (signalChart) signalChart.destroy();

  latencyChart = new Chart(document.getElementById("latencyChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Latency (ms)",
        data: latency,
        borderColor: "#3498db",
        tension: 0.3
      }]
    }
  });

  signalChart = new Chart(document.getElementById("signalChart"), {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Signal Strength",
        data: signal,
        borderColor: "#9b59b6",
        tension: 0.3
      }]
    }
  });
}
