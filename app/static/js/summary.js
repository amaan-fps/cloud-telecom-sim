async function fetchSummary() {
  try {
    const res = await fetch("/api/summary");
    const data = await res.json();

    document.getElementById("sum-total").innerText = data.total_nodes;
    document.getElementById("sum-online").innerText = data.online_nodes;
    document.getElementById("sum-offline").innerText = data.offline_nodes;
    document.getElementById("sum-latency").innerText = data.avg_latency + " ms";

  } catch (e) {
    console.error("Summary fetch failed", e);
  }
}
