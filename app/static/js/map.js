const mapGrid  = document.getElementById("map-grid");
const mapLines = document.getElementById("map-lines");

function clearMap() {
  mapGrid.innerHTML = "";
  mapLines.innerHTML = "";
}

function renderMap(nodes) {
  clearMap();

  if (!nodes || nodes.length === 0) return;

  const width  = mapGrid.clientWidth;
  const height = mapGrid.clientHeight;

  const centerX = width / 2;
  const centerY = height / 2;

  /* ---------------- Collector ---------------- */
  const collector = document.createElement("div");
  collector.className = "map-node node-collector";
  collector.style.left = `${centerX - 55}px`;
  collector.style.top  = `${centerY - 55}px`;
  collector.innerHTML = `
    <div class="node-id">Collector</div>
    <div class="node-status">central</div>
  `;
  mapGrid.appendChild(collector);

  /* ---------------- Base Stations ---------------- */
  const radius = Math.min(width, height) / 2 - 90;
  const angleStep = (2 * Math.PI) / nodes.length;

  nodes.forEach((node, index) => {
    const angle = index * angleStep;

    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle);

    const el = document.createElement("div");
    el.className = `map-node node-${node.status}`;
    el.style.left = `${x - 45}px`;
    el.style.top  = `${y - 45}px`;

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

    /* ---------------- Line ---------------- */
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", centerX);
    line.setAttribute("y1", centerY);
    line.setAttribute("x2", x);
    line.setAttribute("y2", y);
    line.setAttribute("stroke-width", "2");
    line.setAttribute("class", `line-${node.status}`);
    mapLines.appendChild(line);
  });
}
