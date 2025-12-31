let map;
let markers = {}; // node_id -> marker

function initMap() {
  map = L.map("leaflet-map", {
    zoomControl: false
  }).setView([20, 78], 5); // India-ish center (purely visual)

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap"
  }).addTo(map);
}

// Icons
const icons = {
  collector: L.icon({
    iconUrl: "/static/images/collector.png",
    iconSize: [60, 60],
    iconAnchor: [30, 30]
  }),
  base: L.icon({
    iconUrl: "/static/images/base_station.png",
    iconSize: [50, 50],
    iconAnchor: [25, 25]
  })
};

// Fake but stable placement
function getPosition(nodeId) {
  let hash = 0;
  for (let c of nodeId) hash += c.charCodeAt(0);
  return [
    18 + (hash % 10),
    72 + (hash % 15)
  ];
}

function statusColor(status) {
  if (status === "online") return "green";
  if (status === "stale") return "orange";
  return "red";
}

function updateMap(nodes) {
  nodes.forEach(node => {
    if (markers[node.node_id]) {
      markers[node.node_id].setIcon(
        createStatusIcon(node, markers[node.node_id].options.isCollector)
      );
      return;
    }

    const pos = getPosition(node.node_id);
    const isCollector = node.node_id.includes("collector");

    const marker = L.marker(pos, {
      icon: createStatusIcon(node, isCollector),
      isCollector
    }).addTo(map);

    marker.on("click", () => openNodePanel(node.node_id));

    markers[node.node_id] = marker;
  });
}

function createStatusIcon(node, isCollector) {
  return L.divIcon({
    className: "",
    html: `
      <div style="
        position: relative;
        text-align: center;
      ">
        <img src="/static/images/${isCollector ? "collector" : "base_station"}.png"
             style="width:${isCollector ? 60 : 50}px"/>
        <div style="
          position:absolute;
          top:-6px;
          right:-6px;
          width:14px;
          height:14px;
          border-radius:50%;
          background:${statusColor(node.status)};
          border:2px solid white;
        "></div>
      </div>
    `
  });
}
