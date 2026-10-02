// RoMountainAgent Web App Client Logic

const API_BASE = "";

// State
let accessPasscode = localStorage.getItem("app_passcode") || "";
let sessionId = localStorage.getItem("app_session_id");
if (!sessionId) {
  sessionId = "user_" + Math.random().toString(36).substring(2, 10);
  localStorage.setItem("app_session_id", sessionId);
}

// DOM Elements
const authModal = document.getElementById("authModal");
const passcodeInput = document.getElementById("passcodeInput");
const authSubmitBtn = document.getElementById("authSubmitBtn");
const authError = document.getElementById("authError");

const chatContainer = document.getElementById("chatContainer");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const stopBtn = document.getElementById("stopBtn");
const statusIndicator = document.getElementById("statusIndicator");
const clearBtn = document.getElementById("clearBtn");
let currentAbortController = null;

// Markdown simple formatter (converts markdown headers, bold, lists to HTML)
function parseMarkdown(text) {
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Headers
  html = html.replace(/^#### (.*$)/gim, "<h4>$1</h4>");
  html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
  html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");
  html = html.replace(/^# (.*$)/gim, "<h1>$1</h1>");

  // Bold & Italic
  html = html.replace(/\*\*(.*?)\*\*/gim, "<strong>$1</strong>");
  html = html.replace(/\*(.*?)\*/gim, "<em>$1</em>");

  // Unordered list items
  html = html.replace(/^[-\*] (.*$)/gim, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>)/gims, "<ul>$1</ul>");

  // Line breaks to paragraphs
  html = html.replace(/\n\n+/g, "<br><br>");

  return html;
}

// Authentication Check
async function verifyPasscode(code) {
  try {
    const res = await fetch(`${API_BASE}/api/auth`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ passcode: code }),
    });
    return res.ok;
  } catch (err) {
    return false;
  }
}

async function initAuth() {
  if (accessPasscode) {
    const valid = await verifyPasscode(accessPasscode);
    if (valid) {
      authModal.style.display = "none";
      return;
    }
  }
  authModal.style.display = "flex";
  passcodeInput.focus();
}

authSubmitBtn.addEventListener("click", async () => {
  const code = passcodeInput.value.trim();
  if (!code) return;

  authError.style.display = "none";
  authSubmitBtn.disabled = true;
  authSubmitBtn.textContent = "Verifying...";

  const valid = await verifyPasscode(code);
  authSubmitBtn.disabled = false;
  authSubmitBtn.textContent = "Enter Guide";

  if (valid) {
    accessPasscode = code;
    localStorage.setItem("app_passcode", code);
    authModal.style.display = "none";
    messageInput.focus();
  } else {
    authError.textContent = "Invalid passcode. Please try again.";
    authError.style.display = "block";
  }
});

passcodeInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") authSubmitBtn.click();
});

// Render Leaflet Interactive Map Widget (A2A Cartographer)
function renderTrailMap(containerId, mapData) {
  if (typeof L === "undefined") {
    console.warn("Leaflet library is loading...");
    return;
  }

  const centerLat = mapData.center ? mapData.center.lat : 45.5;
  const centerLon = mapData.center ? mapData.center.lon : 25.0;
  const zoom = mapData.zoom || 12;

  const map = L.map(containerId, {
    zoomControl: true,
    scrollWheelZoom: false,
    dragging: true,
    tap: true,
  }).setView([centerLat, centerLon], zoom);

  // Free OpenTopoMap tile layer with attribution
  L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
    maxZoom: 17,
    attribution: "&copy; OpenTopoMap, &copy; OpenStreetMap contributors",
  }).addTo(map);

  const bounds = [];
  const typeColors = {
    trailhead: "#3b82f6",
    cabin: "#f59e0b",
    water: "#06b6d4",
    pass: "#a855f7",
    summit: "#ef4444",
    landmark: "#10b981",
  };

  if (mapData.waypoints && Array.isArray(mapData.waypoints)) {
    mapData.waypoints.forEach((wp) => {
      const color = typeColors[wp.type] || "#10b981";
      const markerHtml = `<div style="
        background-color: ${color};
        width: 14px;
        height: 14px;
        border-radius: 50%;
        border: 2px solid #ffffff;
        box-shadow: 0 0 6px rgba(0,0,0,0.6);
      "></div>`;

      const customIcon = L.divIcon({
        html: markerHtml,
        className: "custom-map-marker",
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      });

      const marker = L.marker([wp.lat, wp.lon], { icon: customIcon }).addTo(map);
      bounds.push([wp.lat, wp.lon]);

      const elevText = wp.elevation ? `<br><span class="map-popup-meta">Elevation: ${wp.elevation}m</span>` : "";
      const descText = wp.description ? `<br><span class="map-popup-meta">${wp.description}</span>` : "";
      marker.bindPopup(`<div class="map-popup-title">${wp.name}</div><span class="map-popup-meta">Type: ${wp.type.toUpperCase()}</span>${elevText}${descText}`);
    });
  }

  // Draw trail polyline if available
  if (mapData.polyline && mapData.polyline.length >= 2) {
    L.polyline(mapData.polyline, {
      color: "#f43f5e",
      weight: 3.5,
      opacity: 0.85,
      dashArray: "6, 6",
    }).addTo(map);
  }

  if (bounds.length > 1) {
    map.fitBounds(bounds, { padding: [25, 25] });
  }

  setTimeout(() => map.invalidateSize(), 300);
}

// Append message card
function appendMessage(role, text, allowExport = false, mapData = null, tokens = null) {
  const msgDiv = document.createElement("div");
  msgDiv.className = `message ${role}`;

  const metaDiv = document.createElement("div");
  metaDiv.className = "message-meta";
  const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  if (role === "user") {
    metaDiv.textContent = `You • ${now}`;
  } else {
    let tokenPillHtml = "";
    if (tokens && (tokens.turn_total > 0 || tokens.session_total > 0)) {
      const turnNum = (tokens.turn_total || 0).toLocaleString();
      const sessNum = (tokens.session_total || 0).toLocaleString();
      const tooltip = `Turn: ${turnNum} tokens (Prompt: ${(tokens.turn_prompt || 0).toLocaleString()}, Output: ${(tokens.turn_candidates || 0).toLocaleString()}) | Session Total: ${sessNum} tokens`;
      tokenPillHtml = `<span class="token-pill" title="${tooltip}">${turnNum} tokens</span>`;
    }
    metaDiv.innerHTML = `<span>RoMountainAgent • ${now}</span>${tokenPillHtml}`;
  }

  const bodyDiv = document.createElement("div");
  bodyDiv.className = "message-body";
  bodyDiv.innerHTML = parseMarkdown(text);

  // Render Interactive Map if mapData was returned by Cartographer Agent
  if (mapData && mapData.waypoints && mapData.waypoints.length > 0) {
    const mapId = "map_" + Math.random().toString(36).substring(2, 10);
    const mapWrapper = document.createElement("div");
    mapWrapper.className = "trail-map-wrapper";
    mapWrapper.innerHTML = `
      <div class="trail-map-header">
        <span>${mapData.trail_name || "Interactive Trail Map"}</span>
        <span class="trail-map-badge">Cartographer Agent • ${mapData.waypoints.length} Waypoints</span>
      </div>
      <div id="${mapId}" class="trail-map-canvas"></div>
      <div class="trail-map-legend">
        <span class="legend-item"><span class="legend-dot trailhead"></span> Trailhead</span>
        <span class="legend-item"><span class="legend-dot cabin"></span> Cabin / Refuge</span>
        <span class="legend-item"><span class="legend-dot water"></span> Water Source</span>
        <span class="legend-item"><span class="legend-dot pass"></span> Saddle / Pass</span>
        <span class="legend-item"><span class="legend-dot summit"></span> Peak / Summit</span>
      </div>
    `;
    bodyDiv.appendChild(mapWrapper);
    setTimeout(() => renderTrailMap(mapId, mapData), 100);
  }

  msgDiv.appendChild(metaDiv);
  msgDiv.appendChild(bodyDiv);

  if (allowExport) {
    const actionsDiv = document.createElement("div");
    actionsDiv.className = "message-actions";

    const exportBtn = document.createElement("button");
    exportBtn.className = "btn-action-small";
    exportBtn.textContent = "[Save Trail Dossier to Phone (.md)]";
    exportBtn.addEventListener("click", () => exportLastHike());

    actionsDiv.appendChild(exportBtn);
    msgDiv.appendChild(actionsDiv);
  }

  chatContainer.appendChild(msgDiv);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Send Message
async function sendMessage(text) {
  if (!text) return;
  appendMessage("user", text);
  messageInput.value = "";

  statusIndicator.textContent = "Guide is analyzing routes, live weather, and Salvamont rules...";
  statusIndicator.style.display = "block";

  // Toggle buttons: Hide Send, Show Stop
  sendBtn.style.display = "none";
  stopBtn.style.display = "inline-block";
  messageInput.disabled = true;

  currentAbortController = new AbortController();

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Access-Passcode": accessPasscode,
      },
      signal: currentAbortController.signal,
      body: JSON.stringify({
        message: text,
        session_id: sessionId,
        user_name: "Mobile Hiker",
      }),
    });

    if (res.status === 401) {
      authModal.style.display = "flex";
      authError.textContent = "Session expired or invalid passcode.";
      authError.style.display = "block";
      return;
    }

    const data = await res.json();
    appendMessage("agent", data.response || "No response received.", true, data.map_data, data.tokens);
  } catch (err) {
    if (err.name === "AbortError") {
      appendMessage("agent", "Response generation was stopped by user.");
    } else {
      appendMessage("agent", `[ERROR] Network error: ${err.message}`);
    }
  } finally {
    currentAbortController = null;
    statusIndicator.style.display = "none";
    sendBtn.style.display = "inline-block";
    stopBtn.style.display = "none";
    sendBtn.disabled = false;
    messageInput.disabled = false;
    messageInput.focus();
  }
}

// Stop Button Event Listener
stopBtn.addEventListener("click", () => {
  if (currentAbortController) {
    currentAbortController.abort();
    currentAbortController = null;
  }
});

// Export Last Hike (triggers direct file download to phone/desktop)
async function exportLastHike() {
  try {
    const res = await fetch(`${API_BASE}/api/export`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Access-Passcode": accessPasscode,
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!res.ok) {
      alert("No recent hike recommendation found to export. Please ask about a trail first.");
      return;
    }

    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition");
    let filename = "Mountain_Trail_Guide.md";
    if (disposition && disposition.indexOf("filename=") !== -1) {
      const match = disposition.match(/filename=["']?([^"';]+)["']?/);
      if (match && match[1]) filename = match[1];
    }

    // Trigger browser download
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.style.display = "none";
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  } catch (err) {
    alert(`Failed to export dossier: ${err.message}`);
  }
}

// Event Listeners
chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = messageInput.value.trim();
  if (text) sendMessage(text);
});

clearBtn.addEventListener("click", async () => {
  if (confirm("Reset conversation memory for this session?")) {
    await fetch(`${API_BASE}/api/clear`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Access-Passcode": accessPasscode,
      },
      body: JSON.stringify({ session_id: sessionId }),
    });
    chatContainer.innerHTML = "";
    appendMessage(
      "agent",
      "Hello! Conversation memory cleared. Tell me what mountain trail you want to explore."
    );
  }
});

// Quick action chips
document.querySelectorAll(".chip-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const action = btn.getAttribute("data-action");
    if (action === "salvamont") {
      sendMessage("What are the official Salvamont mountain safety rules and emergency numbers in Romania?");
    } else if (action === "saved") {
      exportLastHike();
    }
  });
});

// Initial Welcome Message
appendMessage(
  "agent",
  "Hello! I am RoMountainAgent, your intelligent guide for Romanian Carpathian hiking trails.\n\n" +
  "I can help you with:\n" +
  "- Route recommendations by difficulty, duration, and elevation gain\n" +
  "- Live mountain weather at high altitudes and ridge wind alerts\n" +
  "- Turn-by-turn waypoints, potable water points, and mountain shelters\n" +
  "- Official Salvamont safety guidelines and 1-click offline guide downloads\n\n" +
  "Ask me any question below or use the quick buttons above to start planning!"
);

initAuth();
