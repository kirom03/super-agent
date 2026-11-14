/**
 * Super Agent - Interactive Neural DAG Execution Graph Renderer
 * Renders real-time node workflows with animated connections and interactive inspection.
 */

class DAGRenderer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.nodes = new Map(); // id -> node data
    this.links = []; // { source, target, id }
    this.selectedNode = null;
    this.init();
  }

  init() {
    if (!this.container) return;
    this.container.innerHTML = `
      <div class="relative w-full h-full flex flex-col bg-slate-950/60 overflow-hidden">
        <!-- Canvas Top Bar (Clean & Non-overlapping) -->
        <div class="shrink-0 flex items-center justify-between bg-slate-900/90 px-3.5 py-2 border-b border-slate-800/80 text-xs z-10">
          <div class="flex items-center space-x-2">
            <span class="flex items-center text-cyan-400 font-mono text-[11px] font-bold">
              <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping mr-2"></span>
              NEURAL GRAPH
            </span>
            <span class="text-slate-600">|</span>
            <span id="dagNodeCount" class="text-slate-400 font-mono text-[10px]">0 steps</span>
          </div>
          <div class="flex items-center space-x-1.5">
            <button onclick="window.dagRenderer.resetView()" class="px-2 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs flex items-center gap-1 transition" title="Auto Fit">
              <i class="fa-solid fa-arrows-to-dot"></i> Fit
            </button>
            <button onclick="window.dagRenderer.clearGraph()" class="px-2 py-1 rounded-lg bg-slate-800 hover:bg-rose-900/40 text-slate-400 hover:text-rose-400 text-xs flex items-center gap-1 transition" title="Clear">
              <i class="fa-solid fa-trash-can"></i>
            </button>
          </div>
        </div>

        <!-- Node Details Inspector (Floating Modal/Drawer) -->
        <div id="dagInspector" class="hidden absolute bottom-3 left-3 right-3 z-20 glass-panel p-3 rounded-xl border border-cyan-500/40 text-xs shadow-2xl transition">
          <div class="flex items-center justify-between border-b border-slate-700/60 pb-2 mb-2">
            <div class="flex items-center space-x-2">
              <span id="inspectBadge" class="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-cyan-300"></span>
              <span id="inspectTitle" class="font-bold text-white"></span>
            </div>
            <button onclick="window.dagRenderer.closeInspector()" class="text-slate-400 hover:text-white">
              <i class="fa-solid fa-xmark"></i>
            </button>
          </div>
          <div id="inspectContent" class="max-h-36 overflow-y-auto font-mono text-slate-300 space-y-1.5"></div>
        </div>

        <!-- Canvas Body with SVG and Nodes -->
        <div class="relative flex-1 w-full h-full overflow-hidden">
          <!-- SVG Links Layer -->
          <svg id="dagSvg" class="absolute inset-0 w-full h-full pointer-events-none z-0">
            <defs>
              <linearGradient id="flowGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#00f0ff" stop-opacity="0.8" />
                <stop offset="100%" stop-color="#bd00ff" stop-opacity="0.8" />
              </linearGradient>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>
            <g id="dagLinksGroup"></g>
          </svg>

          <!-- HTML Nodes Container -->
          <div id="dagNodesLayer" class="relative w-full h-full z-1 overflow-auto p-6 flex flex-col items-center space-y-7">
            <div id="dagPlaceholder" class="text-slate-500 text-xs text-center mt-20">
              <i class="fa-solid fa-diagram-project text-3xl mb-3 text-slate-700 block"></i>
              Graf eksekusi AI akan muncul di sini secara visual saat perintah dijalankan.
            </div>
          </div>
        </div>
      </div>
    `;

    this.nodesLayer = document.getElementById("dagNodesLayer");
    this.linksGroup = document.getElementById("dagLinksGroup");
    this.svg = document.getElementById("dagSvg");
  }

  clearGraph() {
    this.nodes.clear();
    this.links = [];
    if (this.nodesLayer) {
      this.nodesLayer.innerHTML = `
        <div id="dagPlaceholder" class="text-slate-500 text-xs text-center mt-24">
          <i class="fa-solid fa-diagram-project text-3xl mb-3 text-slate-700 block"></i>
          Graf eksekusi AI akan muncul di sini secara visual saat perintah dijalankan.
        </div>
      `;
    }
    if (this.linksGroup) this.linksGroup.innerHTML = "";
    this.closeInspector();
  }

  resetView() {
    if (this.nodesLayer) {
      this.nodesLayer.scrollTo({ top: 0, behavior: "smooth" });
    }
  }

  updateNode(nodeData) {
    const placeholder = document.getElementById("dagPlaceholder");
    if (placeholder) placeholder.remove();

    const existing = this.nodes.get(nodeData.id);
    const updated = { ...existing, ...nodeData };
    this.nodes.set(nodeData.id, updated);

    const countEl = document.getElementById("dagNodeCount");
    if (countEl) countEl.textContent = `${this.nodes.size} steps`;

    // If parent_id specified, establish link
    if (nodeData.parent_id && !this.links.some(l => l.source === nodeData.parent_id && l.target === nodeData.id)) {
      this.links.push({ source: nodeData.parent_id, target: nodeData.id });
    }

    this.renderNodeElement(updated);
    this.drawLinks();
  }

  getCategoryIcon(cat) {
    switch (cat) {
      case "internet": return '<i class="fa-solid fa-globe text-cyan-400"></i>';
      case "local_system": return '<i class="fa-solid fa-gauge-high text-emerald-400"></i>';
      case "local_file": return '<i class="fa-solid fa-file-code text-purple-400"></i>';
      case "terminal": return '<i class="fa-solid fa-terminal text-amber-400"></i>';
      case "python": return '<i class="fa-brands fa-python text-yellow-400"></i>';
      case "vscode": return '<i class="fa-solid fa-code text-blue-400"></i>';
      case "iot": return '<i class="fa-solid fa-microchip text-pink-400"></i>';
      case "router": return '<i class="fa-solid fa-brain text-fuchsia-400"></i>';
      case "user": return '<i class="fa-solid fa-user-astronaut text-cyan-300"></i>';
      default: return '<i class="fa-solid fa-gear text-slate-400"></i>';
    }
  }

  getStatusBadge(status) {
    if (status === "running") {
      return '<span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>';
    } else if (status === "completed") {
      return '<i class="fa-solid fa-check text-emerald-400 text-[10px]"></i>';
    } else if (status === "error") {
      return '<i class="fa-solid fa-triangle-exclamation text-rose-400 text-[10px]"></i>';
    }
    return '<span class="w-1.5 h-1.5 rounded-full bg-slate-500"></span>';
  }

  renderNodeElement(node) {
    let el = document.getElementById(`dagNode_${node.id}`);
    const isNew = !el;

    if (isNew) {
      el = document.createElement("div");
      el.id = `dagNode_${node.id}`;
      el.className = "w-64 glass-panel rounded-xl p-3 border transition cursor-pointer select-none relative shadow-xl hover:scale-102";
      el.onclick = () => this.inspectNode(node.id);
      this.nodesLayer.appendChild(el);
    }

    // Status styling
    let borderClass = "border-slate-800";
    if (node.status === "running") borderClass = "border-cyan-400 shadow-cyan-500/20 node-running";
    else if (node.status === "completed") borderClass = "border-emerald-500/40 hover:border-emerald-400";
    else if (node.status === "error") borderClass = "border-rose-500/60";

    el.className = `w-64 glass-panel rounded-xl p-3 border ${borderClass} transition cursor-pointer select-none relative shadow-xl`;

    el.innerHTML = `
      <div class="flex items-center justify-between mb-1">
        <div class="flex items-center space-x-2">
          ${this.getCategoryIcon(node.category)}
          <span class="text-xs font-bold text-white truncate max-w-[140px]">${node.label || node.id}</span>
        </div>
        <div class="flex items-center space-x-1">
          ${node.latency_ms ? `<span class="text-[10px] text-slate-400 font-mono">${node.latency_ms}ms</span>` : ''}
          ${this.getStatusBadge(node.status)}
        </div>
      </div>
      ${node.detail ? `<p class="text-[11px] text-slate-300 truncate">${node.detail}</p>` : ''}
      ${node.output_preview ? `<p class="text-[10px] text-slate-400 font-mono truncate bg-slate-950/60 p-1 rounded mt-1">${node.output_preview}</p>` : ''}
    `;

    // Re-draw links on position change
    setTimeout(() => this.drawLinks(), 50);
  }

  drawLinks() {
    if (!this.linksGroup || !this.nodesLayer) return;
    this.linksGroup.innerHTML = "";

    const layerRect = this.nodesLayer.getBoundingClientRect();

    this.links.forEach(link => {
      const srcEl = document.getElementById(`dagNode_${link.source}`);
      const tgtEl = document.getElementById(`dagNode_${link.target}`);
      if (!srcEl || !tgtEl) return;

      const srcRect = srcEl.getBoundingClientRect();
      const tgtRect = tgtEl.getBoundingClientRect();

      const x1 = srcRect.left + srcRect.width / 2 - layerRect.left;
      const y1 = srcRect.bottom - layerRect.top;
      const x2 = tgtRect.left + tgtRect.width / 2 - layerRect.left;
      const y2 = tgtRect.top - layerRect.top;

      const deltaY = y2 - y1;
      const cy1 = y1 + deltaY / 2;
      const cy2 = y2 - deltaY / 2;

      const pathData = `M ${x1} ${y1} C ${x1} ${cy1}, ${x2} ${cy2}, ${x2} ${y2}`;

      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", pathData);
      path.setAttribute("stroke", "url(#flowGradient)");
      path.setAttribute("stroke-width", "2");
      path.setAttribute("fill", "none");
      path.setAttribute("filter", "url(#glow)");
      path.setAttribute("stroke-dasharray", "4, 4");
      this.linksGroup.appendChild(path);
    });
  }

  inspectNode(nodeId) {
    const node = this.nodes.get(nodeId);
    if (!node) return;

    this.selectedNode = node;
    const inspector = document.getElementById("dagInspector");
    const badge = document.getElementById("inspectBadge");
    const title = document.getElementById("inspectTitle");
    const content = document.getElementById("inspectContent");

    badge.textContent = node.category || "NODE";
    title.textContent = node.label || node.id;

    let html = `<div><span class="text-slate-500">Status:</span> <span class="text-cyan-300 uppercase">${node.status}</span></div>`;
    if (node.latency_ms) html += `<div><span class="text-slate-500">Latency:</span> <span class="text-purple-300">${node.latency_ms} ms</span></div>`;
    if (node.args) {
      html += `<div class="mt-1"><span class="text-slate-500">Arguments:</span><pre class="bg-slate-950 p-1.5 rounded text-[10px] text-amber-200 mt-0.5 overflow-x-auto">${JSON.stringify(node.args, null, 2)}</pre></div>`;
    }
    if (node.output_preview) {
      html += `<div class="mt-1"><span class="text-slate-500">Output:</span><pre class="bg-slate-950 p-1.5 rounded text-[10px] text-emerald-300 mt-0.5 overflow-x-auto">${node.output_preview}</pre></div>`;
    }
    if (node.error) {
      html += `<div class="mt-1"><span class="text-rose-400">Error:</span><pre class="bg-rose-950/40 p-1.5 rounded text-[10px] text-rose-300 mt-0.5">${node.error}</pre></div>`;
    }

    content.innerHTML = html;
    inspector.classList.remove("hidden");
  }

  closeInspector() {
    const inspector = document.getElementById("dagInspector");
    if (inspector) inspector.classList.add("hidden");
  }
}
