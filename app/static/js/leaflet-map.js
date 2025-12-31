let map;
let markers = {};       // node_id -> marker
let links = {};         // node_id -> polyline
let nodePositions = {}; // node_id -> [lat, lng]

// Collector anchor (visual only)
const COLLECTOR_ID = "collector";
const COLLECTOR_POS = [22.0, 77.0]; // center-ish India

function initMap() {
  map = L.map("leaflet-map", {
    zoomControl: false
  }).setView(COLLECTOR_POS, 5);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap"
  }).addTo(map);
}

/* ---------------- ICONS ---------------- */

function statusColor(status) {
  if (status === "online") return "#2ecc71";
  if (status === "stale") return "#f39c12";
  return "#e74c3c";
}

function createStatusIcon(node, isCollector) {
  return L.divIcon({
    className: "",
    html: `
      <div style="position: relative; text-align: center;">
        <img src="/static/images/${isCollector ? "collector" : "base_station"}.png"
             style="width:${isCollector ? 60 : 50}px"/>
        <div style="
          position:absolute;
          top:-6px;
          right:-6px;
          width:14px;
          height:14px;
          border-radius:50%;
          background:${statusColor(node.status || "online")};
          border:2px solid white;
        "></div>
      </div>
    `
  });
}

/* ---------------- COLLECTOR ---------------- */

function addCollectorMarker() {
  if (markers[COLLECTOR_ID]) return;

  const marker = L.marker(COLLECTOR_POS, {
    icon: createStatusIcon({ status: "online" }, true),
    isCollector: true
  }).addTo(map);

  marker.on("click", () => openNodePanel(COLLECTOR_ID));
  markers[COLLECTOR_ID] = marker;
}

/* ---------------- POSITIONING ---------------- */

// Stable random placement around collector
function getNodePosition(nodeId) {
  if (nodePositions[nodeId]) return nodePositions[nodeId];

  const angle = Math.random() * Math.PI * 2;
  const radius = 0.8 + Math.random() * 1.5; // degrees-ish

  const lat = COLLECTOR_POS[0] + Math.cos(angle) * radius;
  const lng = COLLECTOR_POS[1] + Math.sin(angle) * radius;

  nodePositions[nodeId] = [lat, lng];
  return nodePositions[nodeId];
}

/* ---------------- LINKS ---------------- */

function createOrUpdateLink(node) {
  const nodeId = node.node_id;
  const from = COLLECTOR_POS;
  const to = nodePositions[nodeId];

  const color = statusColor(node.status);

  if (links[nodeId]) {
    links[nodeId].setStyle({ color });
    return;
  }

  const line = L.polyline([from, to], {
    color,
    weight: 2,
    opacity: 0.8,
    dashArray: node.status === "offline" ? "6,6" : null
  }).addTo(map);

  links[nodeId] = line;
}

/* ---------------- MAIN UPDATE ---------------- */

function updateMap(nodes) {
  addCollectorMarker();

  const seen = new Set();

  nodes.forEach(node => {
    const nodeId = node.node_id;
    seen.add(nodeId);

    // Position
    const pos = getNodePosition(nodeId);

    // Marker
    if (!markers[nodeId]) {
      const marker = L.marker(pos, {
        icon: createStatusIcon(node, false),
        isCollector: false
      }).addTo(map);

      marker.on("click", () => openNodePanel(node));
      markers[nodeId] = marker;
    } else {
      markers[nodeId].setIcon(createStatusIcon(node, false));
    }

    // Link to collector
    createOrUpdateLink(node);
  });

  // Cleanup removed nodes
  Object.keys(markers).forEach(id => {
    if (id === COLLECTOR_ID) return;
    if (!seen.has(id)) {
      map.removeLayer(markers[id]);
      delete markers[id];

      if (links[id]) {
        map.removeLayer(links[id]);
        delete links[id];
      }

      delete nodePositions[id];
    }
  });
}
