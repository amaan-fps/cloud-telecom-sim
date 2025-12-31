let latencyChart = null;
let signalChart = null;

async function loadLatencyChart() {
  const res = await fetch("/api/metrics/latency");
  const data = await res.json();

  const ctx = document.getElementById("globalLatencyChart");

  if (!latencyChart) {
    latencyChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.labels,
        datasets: [{
          label: "Avg Latency (ms)",
          data: data.values,
          borderColor: "#3498db",
          backgroundColor: "rgba(52,152,219,0.2)",
          tension: 0.3,
          fill: true
        }]
      },
      options: {
        responsive: true,
        animation: false,
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  } else {
    latencyChart.data.labels = data.labels;
    latencyChart.data.datasets[0].data = data.values;
    latencyChart.update();
  }
}

async function loadSignalChart() {
  const res = await fetch("/api/metrics/signal");
  const data = await res.json();

  const ctx = document.getElementById("globalSignalChart");

  if (!signalChart) {
    signalChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: data.nodes,
        datasets: [{
          label: "Signal Strength",
          data: data.signals,
          backgroundColor: "#2ecc71"
        }]
      },
      options: {
        responsive: true,
        animation: false,
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  } else {
    signalChart.data.labels = data.nodes;
    signalChart.data.datasets[0].data = data.signals;
    signalChart.update();
  }
}

function startGlobalGraphs() {
  loadLatencyChart();
  loadSignalChart();
  setInterval(() => {
    loadLatencyChart();
    loadSignalChart();
  }, 4000);
}
