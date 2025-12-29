const mapGrid = document.getElementById("map-grid");

function clearMap() {
  mapGrid.innerHTML = "";
}

function renderMap(nodes) {
  clearMap();

  const width = mapGrid.clientWidth;
  const height = mapGrid.clientHeight;

  nodes.forEach((node, index) => {
    const el = document.createElement("div");
    el.className = `map-node node-${node.status}`;

    // simple grid placement (we'll improve later)
    const cols = Math.ceil(Math.sqrt(nodes.length));
    const size = 100;
    const x = (index % cols) * size + 20;
    const y = Math.floor(index / cols) * size + 20;

    el.style.left = `${x}px`;
    el.style.top = `${y}px`;

    el.innerHTML = `
      <div class="node-id">${node.node_id}</div>
      <div class="node-status">${node.status}</div>
    `;

    el.onclick = () => {
      alert(
        `Node: ${node.node_id}\n` +
        `Status: ${node.status}\n` +
        `Latency: ${node.latency_ms} ms\n` +
        `Loss: ${node.packet_loss}`
      );
    };

    mapGrid.appendChild(el);
  });
}
