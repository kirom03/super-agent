/**
 * Super Agent Main Dashboard Application Logic
 * Integrates SSE streaming, 9Router controls, System telemetry, and Sandbox previews.
 */

let isStreaming = false;
let currentThinkingBlock = null;
let currentMessageCard = null;
let attachedImages = [];

document.addEventListener("DOMContentLoaded", () => {
  // Initialize DAG Renderer
  window.dagRenderer = new DAGRenderer("dagCanvasContainer");

  // Fetch initial telemetry & status
  fetchRouterStatus();
  fetchTelemetry();
  fetchSandboxFiles();
  fetchVSCodeStatus();

  // Polling timers
  setInterval(fetchTelemetry, 3500);
  setInterval(fetchSandboxFiles, 8000);
  setInterval(pollSimulatorStatus, 4000);

  // Setup tabs
  setupTabs();
  fetchSkills();
  fetchScheduledTasks();

  // Setup prompt form
  const form = document.getElementById("chatForm");
  if (form) {
    form.addEventListener("submit", handleChatSubmit);
  }

  // Setup Clipboard Paste & Drag-and-Drop for Screenshots / Photos
  setupImageClipboardAndDragDrop();

  // Setup Global Keyboard Shortcuts (Ctrl+K, etc.)
  setupKeyboardShortcuts();
});

// Panel Toggle Functions
function toggleLeftPanel() {
  const panel = document.getElementById("leftSidebar");
  const btn = document.getElementById("btnToggleLeft");
  if (!panel) return;
  panel.classList.toggle("collapsed");
  if (btn) {
    btn.classList.toggle("text-cyan-400", !panel.classList.contains("collapsed"));
  }
}

function toggleRightPanel() {
  const panel = document.getElementById("rightSidebar");
  const btn = document.getElementById("btnToggleRight");
  if (!panel) return;
  panel.classList.toggle("collapsed");
  if (btn) {
    btn.classList.toggle("text-cyan-400", !panel.classList.contains("collapsed"));
  }
  if (!panel.classList.contains("collapsed") && window.dagRenderer) {
    setTimeout(() => window.dagRenderer.drawLinks(), 300);
  }
}

// Command Palette Logic
const PALETTE_COMMANDS = [
  { id: "model-sonnet", title: "Ganti Model ke Claude Sonnet 4.6", cat: "Model", icon: "fa-brain", action: () => selectModelByName("ag/claude-sonnet-4-6") },
  { id: "model-flash", title: "Ganti Model ke Gemini 3.8 Flash Low (Cepat)", cat: "Model", icon: "fa-bolt", action: () => selectModelByName("ag/gemini-3.8-flash-low") },
  { id: "model-opus", title: "Ganti Model ke Claude Opus Thinking", cat: "Model", icon: "fa-lightbulb", action: () => selectModelByName("ag/claude-opus-4-6-thinking") },
  { id: "tab-dag", title: "Buka Tab: DAG Neural Graph", cat: "Navigasi", icon: "fa-diagram-project", action: () => switchTab("Dag") },
  { id: "tab-prev", title: "Buka Tab: Live Web Preview", cat: "Navigasi", icon: "fa-eye", action: () => switchTab("Preview") },
  { id: "tab-skills", title: "Buka Tab: Active Skills Hub", cat: "Navigasi", icon: "fa-wand-magic-sparkles", action: () => switchTab("Skills") },
  { id: "tab-tasks", title: "Buka Tab: Task Scheduler", cat: "Navigasi", icon: "fa-clock", action: () => switchTab("Scheduler") },
  { id: "tab-code", title: "Buka Tab: Code Inspector", cat: "Navigasi", icon: "fa-code", action: () => switchTab("Code") },
  { id: "iot-scan", title: "Scan USB Serial Mikrokontroler (ESP32/Arduino)", cat: "Hardware", icon: "fa-satellite-dish", action: () => scanSerialPorts() },
  { id: "relay-on", title: "Nyalakan MQTT Relay (ON)", cat: "IoT", icon: "fa-toggle-on", action: () => quickMqtt('super_agent/laptop/relay', 'ON') },
  { id: "relay-off", title: "Matikan MQTT Relay (OFF)", cat: "IoT", icon: "fa-toggle-off", action: () => quickMqtt('super_agent/laptop/relay', 'OFF') },
  { id: "toggle-left", title: "Toggle Sembunyikan/Tampilkan Panel Kiri", cat: "Tampilan", icon: "fa-table-columns", action: () => toggleLeftPanel() },
  { id: "toggle-right", title: "Toggle Sembunyikan/Tampilkan Panel Kanan", cat: "Tampilan", icon: "fa-chart-line", action: () => toggleRightPanel() },
  { id: "reset-chat", title: "Reset Seluruh Sesi Percakapan & Graf", cat: "Sesi", icon: "fa-rotate-left", action: () => resetSession() }
];

let selectedCmdIndex = 0;
let filteredCommands = [...PALETTE_COMMANDS];

function setupKeyboardShortcuts() {
  document.addEventListener("keydown", (e) => {
    // Ctrl + K or Cmd + K
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      toggleCommandPalette();
    }
    // Escape closes modal
    if (e.key === "Escape") {
      const modal = document.getElementById("cmdPaletteModal");
      if (modal && !modal.classList.contains("hidden")) {
        toggleCommandPalette();
      }
    }
  });
}

function toggleCommandPalette() {
  const modal = document.getElementById("cmdPaletteModal");
  if (!modal) return;
  const isHidden = modal.classList.toggle("hidden");
  if (!isHidden) {
    const input = document.getElementById("cmdPaletteInput");
    input.value = "";
    filterCommandPalette("");
    setTimeout(() => input.focus(), 50);
  }
}

function filterCommandPalette(query) {
  const q = query.toLowerCase().trim();
  filteredCommands = PALETTE_COMMANDS.filter(cmd => 
    cmd.title.toLowerCase().includes(q) || cmd.cat.toLowerCase().includes(q)
  );
  selectedCmdIndex = 0;
  renderCommandList();
}

function renderCommandList() {
  const container = document.getElementById("cmdPaletteResults");
  if (!container) return;

  if (filteredCommands.length === 0) {
    container.innerHTML = `<div class="p-4 text-center text-slate-500 italic">Tidak ada perintah yang cocok.</div>`;
    return;
  }

  container.innerHTML = filteredCommands.map((cmd, idx) => `
    <div 
      onclick="executePaletteCommand(${idx})" 
      class="cmd-item p-2.5 rounded-xl border border-transparent cursor-pointer flex items-center justify-between ${idx === selectedCmdIndex ? 'active' : ''}"
    >
      <div class="flex items-center space-x-3">
        <div class="w-7 h-7 rounded-lg bg-slate-900 border border-slate-700/60 flex items-center justify-center text-cyan-400">
          <i class="fa-solid ${cmd.icon}"></i>
        </div>
        <div>
          <span class="text-xs font-medium text-slate-200">${cmd.title}</span>
          <span class="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono">${cmd.cat}</span>
        </div>
      </div>
      <i class="fa-solid fa-arrow-turn-down text-slate-600 text-xs rotate-90"></i>
    </div>
  `).join('');
}

function handleCommandKey(e) {
  if (e.key === "ArrowDown") {
    e.preventDefault();
    if (filteredCommands.length > 0) {
      selectedCmdIndex = (selectedCmdIndex + 1) % filteredCommands.length;
      renderCommandList();
    }
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    if (filteredCommands.length > 0) {
      selectedCmdIndex = (selectedCmdIndex - 1 + filteredCommands.length) % filteredCommands.length;
      renderCommandList();
    }
  } else if (e.key === "Enter") {
    e.preventDefault();
    executePaletteCommand(selectedCmdIndex);
  }
}

function executePaletteCommand(idx) {
  const cmd = filteredCommands[idx];
  if (cmd && typeof cmd.action === "function") {
    toggleCommandPalette();
    cmd.action();
  }
}

function selectModelByName(modelName) {
  const sel = document.getElementById("routerModelSelect");
  if (sel) {
    sel.value = modelName;
    handleModelChange({ target: sel });
  }
}

// Setup Right Panel Tabs (DAG vs Live Preview vs Skills vs Scheduler vs Code Inspector)
function setupTabs() {
  const tabs = ["tabDag", "tabPreview", "tabSkills", "tabScheduler", "tabCode"];
  const panes = ["paneDag", "panePreview", "paneSkills", "paneScheduler", "paneCode"];

  tabs.forEach((tabId, idx) => {
    const btn = document.getElementById(tabId);
    if (!btn) return;
    btn.addEventListener("click", () => {
      tabs.forEach((t, i) => {
        const b = document.getElementById(t);
        const p = document.getElementById(panes[i]);
        if (i === idx) {
          b.className = "px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40";
          p.classList.remove("hidden");
        } else {
          b.className = "px-2.5 py-1.5 rounded-lg text-xs text-slate-400 hover:text-white";
          p.classList.add("hidden");
        }
      });
      if (tabId === "tabDag" && window.dagRenderer) {
        setTimeout(() => window.dagRenderer.drawLinks(), 100);
      }
    });
  });
}

// Switch directly to a specific tab
function switchTab(targetTab) {
  const btn = document.getElementById(`tab${targetTab}`);
  if (btn) btn.click();
}

// 9Router Status & Model Switcher
async function fetchRouterStatus() {
  try {
    const res = await fetch("/api/router/status");
    const data = await res.json();

    const statusBadge = document.getElementById("routerStatusBadge");
    const latencyBadge = document.getElementById("routerLatency");
    const modelSelect = document.getElementById("routerModelSelect");

    if (data.status && data.status.online) {
      statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 mr-1.5"></span> 9Router Online`;
      latencyBadge.textContent = `${data.status.latency_ms} ms`;
    } else {
      statusBadge.innerHTML = `<span class="w-2 h-2 rounded-full bg-rose-400 mr-1.5"></span> 9Router Offline`;
      latencyBadge.textContent = "ERR";
    }

    if (modelSelect && data.models) {
      modelSelect.innerHTML = "";
      data.models.forEach(m => {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = `${m.id} (${m.owned_by || 'ai'})`;
        if (m.id === data.active_model) opt.selected = true;
        modelSelect.appendChild(opt);
      });
    }
  } catch (err) {
    console.error("Router status error:", err);
  }
}

async function handleModelChange(e) {
  const newModel = e.target.value;
  try {
    const res = await fetch("/api/router/set-model", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model: newModel })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(`Model dialihkan ke: ${newModel}`);
    }
  } catch (err) {
    alert("Gagal mengubah model: " + err.message);
  }
}

// Laptop System Telemetry
async function fetchTelemetry() {
  try {
    const res = await fetch("/api/system/telemetry");
    const data = await res.json();
    if (data.status !== "success") return;

    // CPU gauge
    const cpuVal = data.cpu.usage_percent;
    document.getElementById("cpuGaugeVal").textContent = `${cpuVal}%`;
    document.getElementById("cpuProgressBar").style.width = `${Math.min(cpuVal, 100)}%`;

    // RAM gauge
    const ramVal = data.ram.used_percent;
    document.getElementById("ramGaugeVal").textContent = `${ramVal}%`;
    document.getElementById("ramGaugeDetail").textContent = `${data.ram.used_gb} / ${data.ram.total_gb} GB`;
    document.getElementById("ramProgressBar").style.width = `${Math.min(ramVal, 100)}%`;

    // Battery
    const bat = data.battery;
    if (bat && bat.percent !== undefined) {
      const batEl = document.getElementById("batteryStatus");
      batEl.innerHTML = `<i class="fa-solid fa-battery-${bat.percent > 70 ? 'full' : (bat.percent > 30 ? 'half' : 'quarter')} ${bat.charging ? 'text-emerald-400' : 'text-slate-300'} mr-1"></i> ${bat.percent}% ${bat.charging ? '⚡' : ''}`;
    }

    // Disk D: or C:
    if (data.disks && data.disks.length > 0) {
      const diskList = document.getElementById("diskList");
      diskList.innerHTML = data.disks.map(d => `
        <div class="flex items-center justify-between text-[11px] font-mono bg-slate-950/60 p-1.5 rounded border border-slate-800">
          <span class="text-cyan-300 font-bold">${d.mountpoint}</span>
          <span class="text-slate-400">${d.free_gb} GB Free (${d.used_percent}%)</span>
        </div>
      `).join('');
    }
  } catch (err) {
    // Silent telemetry retry
  }
}

// VS Code Status
async function fetchVSCodeStatus() {
  try {
    const res = await fetch("/api/vscode/status");
    const data = await res.json();
    const el = document.getElementById("vscodeStatusBadge");
    if (el) {
      if (data.vscode_running) {
        el.innerHTML = `<i class="fa-solid fa-code text-blue-400 mr-1"></i> VS Code Active`;
      } else {
        el.innerHTML = `<i class="fa-solid fa-code text-slate-500 mr-1"></i> VS Code Standby`;
      }
    }
  } catch (err) {}
}

// Sandbox Files Explorer
async function fetchSandboxFiles() {
  try {
    const res = await fetch("/api/sandbox/files");
    const data = await res.json();
    const listEl = document.getElementById("sandboxFileList");
    if (!listEl) return;

    if (!data.items || data.items.length === 0) {
      listEl.innerHTML = `<span class="text-slate-500 italic text-[11px]">Belum ada file di sandbox.</span>`;
      return;
    }

    listEl.innerHTML = data.items.map(item => `
      <div class="flex items-center justify-between p-2 rounded-lg bg-slate-950/60 hover:bg-slate-900 border border-slate-800 transition">
        <div class="flex items-center space-x-2 truncate cursor-pointer" onclick="viewFileContent('${item.name}')">
          <i class="fa-solid ${item.is_directory ? 'fa-folder text-amber-400' : 'fa-file-code text-cyan-400'} text-xs"></i>
          <span class="text-xs text-slate-200 truncate font-mono">${item.name}</span>
        </div>
        <div class="flex items-center space-x-1 shrink-0">
          ${!item.is_directory && item.name.endsWith('.html') ? `
            <button onclick="previewFileInFrame('${item.name}')" title="Live Web Preview" class="p-1 rounded text-cyan-400 hover:text-white text-xs">
              <i class="fa-solid fa-play"></i>
            </button>
          ` : ''}
          <button onclick="openInVSCode('${item.name}')" title="Buka di VS Code" class="p-1 rounded text-blue-400 hover:text-white text-xs">
            <i class="fa-solid fa-arrow-up-right-from-square"></i>
          </button>
        </div>
      </div>
    `).join('');
  } catch (err) {}
}

// View file in Code Inspector
async function viewFileContent(filename) {
  try {
    const res = await fetch(`/api/sandbox/file?path=${encodeURIComponent(filename)}`);
    const data = await res.json();
    if (data.status === "success") {
      switchTab("Code");
      document.getElementById("codeFileName").textContent = filename;
      const codeBlock = document.getElementById("codeViewerContent");
      codeBlock.textContent = data.content;
      if (window.hljs) hljs.highlightElement(codeBlock);
    }
  } catch (err) {
    alert("Gagal membaca file: " + err.message);
  }
}

// Open Live Preview Frame
function previewFileInFrame(filename) {
  switchTab("Preview");
  const iframe = document.getElementById("previewFrame");
  iframe.src = `/api/sandbox/preview/${encodeURIComponent(filename)}`;
  document.getElementById("previewUrlLabel").textContent = `http://localhost:7860/api/sandbox/preview/${filename}`;
}

// Open File directly in VS Code
async function openInVSCode(filename) {
  try {
    const res = await fetch("/api/vscode/open", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filepath: filename })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(`File dibuka di VS Code!`);
    } else {
      alert("Error: " + data.error);
    }
  } catch (err) {
    alert("Gagal membuka di VS Code: " + err.message);
  }
}

// Serial COM Ports Scan
async function scanSerialPorts() {
  const container = document.getElementById("serialPortList");
  container.innerHTML = `<span class="text-cyan-400 animate-pulse text-[11px]">Scanning USB ports...</span>`;
  try {
    const res = await fetch("/api/iot/scan-serial");
    const data = await res.json();
    if (data.status === "success" && data.ports && data.ports.length > 0) {
      container.innerHTML = data.ports.map(p => `
        <div class="p-1.5 rounded bg-slate-900 border border-slate-800 text-[11px]">
          <span class="font-bold text-cyan-300">${p.port}</span>: ${p.description}
        </div>
      `).join('');
    } else {
      container.innerHTML = `<span class="text-slate-500 text-[11px]">Tidak ada port USB COM terdeteksi.</span>`;
    }
  } catch (err) {
    container.innerHTML = `<span class="text-rose-400 text-[11px]">Error scanning ports.</span>`;
  }
}

// Quick MQTT Publish
async function quickMqtt(topic, payload) {
  try {
    const res = await fetch("/api/iot/mqtt", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ topic, payload })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast(`MQTT [${topic}] -> ${payload}`);
    }
  } catch (err) {}
}

// Quick Prompt sender
function sendQuickPrompt(promptText) {
  const input = document.getElementById("userInput");
  input.value = promptText;
  handleChatSubmit(new Event("submit"));
}

// Reset Conversation
async function resetSession() {
  if (!confirm("Reset seluruh percakapan dan graph?")) return;
  try {
    await fetch("/api/chat/reset", { method: "POST" });
    document.getElementById("chatStream").innerHTML = "";
    if (window.dagRenderer) window.dagRenderer.clearGraph();
    showToast("Sesi berhasil di-reset.");
  } catch (err) {}
}

// Image Upload & Clipboard Paste System
function handleImageFileSelect(e) {
  const files = e.target.files;
  if (!files || files.length === 0) return;
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    if (file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (loadEvt) => {
        attachedImages.push(loadEvt.target.result);
        renderImagePreviews();
      };
      reader.readAsDataURL(file);
    }
  }
  e.target.value = "";
}

function setupImageClipboardAndDragDrop() {
  // Listen for paste event on document and input field
  window.addEventListener("paste", (e) => {
    const items = (e.clipboardData || e.originalEvent?.clipboardData)?.items;
    if (!items) return;

    let hasImage = false;
    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf("image") !== -1) {
        const file = items[i].getAsFile();
        if (file) {
          hasImage = true;
          const reader = new FileReader();
          reader.onload = (loadEvt) => {
            attachedImages.push(loadEvt.target.result);
            renderImagePreviews();
            showToast("📷 Screenshot ditempel dari clipboard!");
          };
          reader.readAsDataURL(file);
        }
      }
    }
    if (hasImage) {
      e.preventDefault();
    }
  });

  // Drag and drop onto chat form
  const dropZone = document.getElementById("chatForm");
  if (dropZone) {
    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.classList.add("border-cyan-400");
    });
    dropZone.addEventListener("dragleave", (e) => {
      e.preventDefault();
      dropZone.classList.remove("border-cyan-400");
    });
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.classList.remove("border-cyan-400");
      const files = e.dataTransfer?.files;
      if (files) {
        for (let i = 0; i < files.length; i++) {
          if (files[i].type.startsWith("image/")) {
            const reader = new FileReader();
            reader.onload = (loadEvt) => {
              attachedImages.push(loadEvt.target.result);
              renderImagePreviews();
            };
            reader.readAsDataURL(files[i]);
          }
        }
      }
    });
  }
}

function renderImagePreviews() {
  const container = document.getElementById("imagePreviewContainer");
  const badge = document.getElementById("imageCountBadge");
  if (!container) return;

  if (attachedImages.length === 0) {
    container.innerHTML = "";
    container.classList.add("hidden");
    if (badge) badge.classList.add("hidden");
    return;
  }

  container.classList.remove("hidden");
  if (badge) {
    badge.textContent = attachedImages.length;
    badge.classList.remove("hidden");
  }

  container.innerHTML = attachedImages.map((img, idx) => `
    <div class="relative group shrink-0">
      <img src="${img}" class="w-16 h-16 object-cover rounded-xl border border-cyan-500/50 shadow-md bg-slate-900" />
      <button 
        type="button" 
        onclick="removeAttachedImage(${idx})" 
        class="absolute -top-1.5 -right-1.5 w-5 h-5 bg-rose-600 hover:bg-rose-500 text-white rounded-full flex items-center justify-center text-[10px] shadow cursor-pointer"
        title="Hapus foto"
      >
        <i class="fa-solid fa-xmark"></i>
      </button>
    </div>
  `).join("");
}

function removeAttachedImage(idx) {
  attachedImages.splice(idx, 1);
  renderImagePreviews();
}

// Handle User Chat Submit via SSE Stream
async function handleChatSubmit(e) {
  if (e) e.preventDefault();
  if (isStreaming) return;

  const input = document.getElementById("userInput");
  const prompt = input.value.trim();
  const imagesToSend = [...attachedImages];

  if (!prompt && imagesToSend.length === 0) return;

  input.value = "";
  attachedImages = [];
  renderImagePreviews();

  isStreaming = true;
  document.getElementById("sendBtn").disabled = true;
  document.getElementById("sendBtn").innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;

  // Render User Message Card with images
  appendUserMessage(prompt, imagesToSend);

  // Clear or prepare DAG graph
  if (window.dagRenderer) {
    window.dagRenderer.clearGraph();
  }

  // Create Assistant Streaming Message Card
  const assistantCard = createAssistantCard();
  const streamContainer = document.getElementById("chatStream");
  streamContainer.appendChild(assistantCard);
  streamContainer.scrollTo({ top: streamContainer.scrollHeight, behavior: "smooth" });

  const modelSelect = document.getElementById("routerModelSelect");
  const chosenModel = modelSelect ? modelSelect.value : null;

  try {
    const response = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, images: imagesToSend, model: chosenModel })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${await response.text()}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop(); // keep remainder

      for (const block of lines) {
        if (block.startsWith("data: ")) {
          try {
            const eventData = JSON.parse(block.replace("data: ", "").trim());
            handleServerEvent(eventData, assistantCard);
          } catch (pErr) {
            console.error("Parse event error:", pErr);
          }
        }
      }
    }
  } catch (err) {
    appendErrorCard(err.message);
  } finally {
    isStreaming = false;
    document.getElementById("sendBtn").disabled = false;
    document.getElementById("sendBtn").innerHTML = `<span>Kirim</span><i class="fa-solid fa-paper-plane text-xs"></i>`;
    fetchSandboxFiles();
  }
}

function handleServerEvent(event, card) {
  const textBody = card.querySelector(".agent-text-body");
  const toolsContainer = card.querySelector(".agent-tools-container");
  const thinkingContainer = card.querySelector(".agent-thinking-container");

  switch (event.type) {
    case "node_update":
      if (window.dagRenderer) {
        window.dagRenderer.updateNode(event.node);
      }
      break;

    case "thinking_start":
      thinkingContainer.classList.remove("hidden");
      thinkingContainer.querySelector(".thinking-status").textContent = event.message;
      break;

    case "thinking_content":
      thinkingContainer.classList.remove("hidden");
      const thinkingBody = thinkingContainer.querySelector(".thinking-body");
      thinkingBody.textContent += event.content;
      break;

    case "tool_start":
      const toolEl = document.createElement("div");
      toolEl.id = `tool_ui_${event.step}_${event.tool_name}`;
      toolEl.className = "p-2 rounded-xl bg-slate-900/90 border border-slate-700/60 text-xs mb-2 shadow-lg";
      toolEl.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <div class="flex items-center space-x-2">
            <span class="w-2 h-2 rounded-full bg-cyan-400 animate-ping"></span>
            <span class="font-bold text-cyan-300 font-mono">${event.tool_name}</span>
          </div>
          <span class="text-[10px] text-slate-400 uppercase font-mono">${event.category || 'tool'}</span>
        </div>
        <div class="text-[11px] text-slate-400 truncate font-mono bg-slate-950 p-1 rounded">
          ${JSON.stringify(event.args)}
        </div>
      `;
      toolsContainer.appendChild(toolEl);
      break;

    case "tool_end":
      const existingTool = document.getElementById(`tool_ui_${event.step}_${event.tool_name}`);
      if (existingTool) {
        const isErr = event.status === "error";
        existingTool.className = `p-2 rounded-xl bg-slate-900/90 border ${isErr ? 'border-rose-500/60' : 'border-emerald-500/40'} text-xs mb-2 shadow-lg`;
        existingTool.innerHTML = `
          <div class="flex items-center justify-between mb-1">
            <div class="flex items-center space-x-2">
              <i class="fa-solid ${isErr ? 'fa-xmark text-rose-400' : 'fa-check text-emerald-400'}"></i>
              <span class="font-bold text-white font-mono">${event.tool_name}</span>
            </div>
            <span class="text-[10px] text-slate-400 font-mono">${event.latency_ms} ms</span>
          </div>
          <details class="text-[11px] text-slate-300 font-mono bg-slate-950 p-1.5 rounded mt-1">
            <summary class="cursor-pointer text-cyan-400 hover:text-cyan-300">Lihat Output (${event.output ? event.output.length : 0} bytes)</summary>
            <pre class="mt-1 whitespace-pre-wrap max-h-40 overflow-y-auto text-[10px] text-slate-300">${event.output}</pre>
          </details>
        `;
      }
      break;

    case "token":
      if (window.marked) {
        card.rawText = (card.rawText || "") + event.content;
        textBody.innerHTML = marked.parse(card.rawText);
        if (window.hljs) {
          textBody.querySelectorAll("pre code").forEach(el => hljs.highlightElement(el));
        }
      } else {
        textBody.textContent += event.content;
      }
      break;

    case "done":
      card.querySelector(".agent-header-status").innerHTML = `<span class="text-emerald-400 text-xs font-mono">✓ Selesai (${event.latency_sec || 0}s)</span>`;
      break;

    case "error":
      const errBox = document.createElement("div");
      errBox.className = "p-3 rounded-xl bg-rose-950/80 border border-rose-800 text-xs text-rose-200 mt-2";
      errBox.innerHTML = `<strong>Error:</strong> ${event.message}`;
      textBody.appendChild(errBox);
      break;
  }

  const streamContainer = document.getElementById("chatStream");
  streamContainer.scrollTo({ top: streamContainer.scrollHeight, behavior: "smooth" });
}

function appendUserMessage(text, images = []) {
  const container = document.getElementById("chatStream");
  const el = document.createElement("div");
  el.className = "flex items-start justify-end space-x-3 mb-4";
  
  let imagesHtml = '';
  if (images && images.length > 0) {
    imagesHtml = `
      <div class="flex flex-wrap gap-2 mb-2 justify-end">
        ${images.map(img => `
          <img src="${img}" class="max-h-48 max-w-xs rounded-xl border border-cyan-500/40 shadow-lg object-contain bg-slate-950/80 cursor-pointer hover:scale-102 transition" onclick="window.open('${img}', '_blank')" alt="Screenshot" />
        `).join('')}
      </div>
    `;
  }

  el.innerHTML = `
    <div class="glass-panel p-4 rounded-2xl max-w-2xl border-cyan-500/30 text-sm text-slate-100 bg-cyan-950/30">
      <div class="flex items-center space-x-2 mb-1 justify-end">
        <span class="text-xs font-bold text-cyan-300 font-mono">User</span>
        <i class="fa-solid fa-user-astronaut text-cyan-400 text-xs"></i>
      </div>
      ${imagesHtml}
      ${text ? `<p class="leading-relaxed whitespace-pre-wrap">${text}</p>` : ''}
    </div>
  `;
  container.appendChild(el);
  container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
}

function createAssistantCard() {
  const el = document.createElement("div");
  el.className = "flex items-start space-x-3 mb-6 max-w-3xl";
  el.innerHTML = `
    <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-600 to-fuchsia-500 flex items-center justify-center shrink-0 shadow-lg shadow-cyan-500/20">
      <i class="fa-solid fa-brain text-white text-sm"></i>
    </div>
    <div class="glass-panel p-5 rounded-2xl flex-1 border border-slate-800 text-sm leading-relaxed shadow-2xl space-y-3">
      <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
        <div class="flex items-center space-x-2">
          <span class="font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-fuchsia-400">Super Agent</span>
          <span class="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">9Router ReAct</span>
        </div>
        <div class="agent-header-status text-xs text-slate-400 font-mono flex items-center space-x-1">
          <i class="fa-solid fa-circle-notch fa-spin text-cyan-400"></i>
          <span>Thinking...</span>
        </div>
      </div>

      <!-- Thinking Drawer (Collapsible) -->
      <div class="agent-thinking-container hidden thinking-box rounded-xl p-3 text-xs">
        <details>
          <summary class="cursor-pointer font-bold text-purple-300 flex items-center justify-between">
            <span class="thinking-status">Reasoning & Perencanaan</span>
            <i class="fa-solid fa-chevron-down text-[10px]"></i>
          </summary>
          <pre class="thinking-body mt-2 whitespace-pre-wrap font-mono text-[11px] text-slate-300 max-h-36 overflow-y-auto"></pre>
        </details>
      </div>

      <!-- Tool Execution Cards Container -->
      <div class="agent-tools-container"></div>

      <!-- Agent Markdown Text Body -->
      <div class="agent-text-body prose prose-cyber prose-invert text-slate-200 text-sm leading-relaxed"></div>
    </div>
  `;
  return el;
}

function appendErrorCard(msg) {
  const container = document.getElementById("chatStream");
  const el = document.createElement("div");
  el.className = "p-4 rounded-2xl bg-rose-950/80 border border-rose-700 text-sm text-rose-200 mb-4";
  el.innerHTML = `<strong>Error:</strong> ${msg}`;
  container.appendChild(el);
}

// Simple Toast Notification
function showToast(msg) {
  const toast = document.createElement("div");
  toast.className = "fixed bottom-5 right-5 z-50 glass-panel px-4 py-2.5 rounded-xl border border-cyan-500/50 text-xs text-cyan-300 shadow-2xl flex items-center space-x-2 animate-bounce";
  toast.innerHTML = `<i class="fa-solid fa-circle-check text-emerald-400"></i> <span>${msg}</span>`;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 3200);
}

// Fetch and render Skills
async function fetchSkills() {
  try {
    const res = await fetch("/api/skills");
    const skills = await res.json();
    const container = document.getElementById("skillsContainer");
    if (!container) return;

    if (!skills || skills.length === 0) {
      container.innerHTML = `<div class="text-xs text-slate-500 italic">Tidak ada skill terpasang.</div>`;
      return;
    }

    container.innerHTML = skills.map(s => `
      <div class="p-3 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/40 transition">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-bold text-white">${s.displayName || s.name}</span>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 uppercase">${s.risk || 'safe'}</span>
        </div>
        <p class="text-[11px] text-slate-400 mb-2 leading-relaxed">${s.description || ''}</p>
        <div class="flex items-center justify-between text-[10px] font-mono text-slate-500">
          <span>v${s.version || '1.0.0'}</span>
          <button onclick="sendQuickPrompt('Jalankan skill: ${s.name}')" class="text-cyan-400 hover:text-cyan-300 font-bold">Aktifkan →</button>
        </div>
      </div>
    `).join('');
  } catch (err) {}
}

// Fetch and render Scheduled Tasks
async function fetchScheduledTasks() {
  try {
    const res = await fetch("/api/scheduler/tasks");
    const tasks = await res.json();
    const container = document.getElementById("tasksContainer");
    if (!container) return;

    container.innerHTML = tasks.map(t => `
      <div class="p-3 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-amber-500/40 transition">
        <div class="flex items-center justify-between mb-1">
          <span class="text-xs font-bold text-white">${t.title}</span>
          <label class="relative inline-flex items-center cursor-pointer">
            <input type="checkbox" ${t.enabled ? 'checked' : ''} onchange="toggleScheduledTask('${t.id}', this.checked)" class="sr-only peer">
            <div class="w-8 h-4 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-amber-500"></div>
          </label>
        </div>
        <p class="text-[11px] text-slate-400 mb-2 leading-relaxed">${t.prompt}</p>
        <div class="text-[10px] font-mono text-slate-500 flex items-center justify-between">
          <span>Interval: ${t.interval_seconds}s</span>
          <span class="${t.enabled ? 'text-emerald-400' : 'text-slate-500'}">${t.enabled ? 'ACTIVE' : 'IDLE'}</span>
        </div>
      </div>
    `).join('');
  } catch (err) {}
}

async function toggleScheduledTask(taskId, enabled) {
  try {
    await fetch("/api/scheduler/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ task_id: taskId, enabled })
    });
    showToast(`Task ${taskId} ${enabled ? 'diaktifkan' : 'dinonaktifkan'}`);
  } catch (err) {}
}

// Virtual ESP32 Simulator Controls
async function toggleVirtualSimulator() {
  try {
    const res = await fetch("/api/simulator/esp32/toggle", { method: "POST" });
    const data = await res.json();
    updateSimulatorUI(data);
    showToast(data.running ? "Virtual ESP32 aktif!" : "Virtual ESP32 dimatikan");
  } catch (err) {}
}

async function pollSimulatorStatus() {
  try {
    const res = await fetch("/api/simulator/esp32/status");
    const data = await res.json();
    updateSimulatorUI(data);
  } catch (err) {}
}

function updateSimulatorUI(data) {
  const btn = document.getElementById("toggleSimulatorBtn");
  const statusEl = document.getElementById("simStatus");
  const relayEl = document.getElementById("simRelay");
  const sensorEl = document.getElementById("simSensors");

  if (!btn || !statusEl) return;

  if (data.running) {
    btn.textContent = "Stop Node";
    btn.className = "px-2.5 py-1 rounded text-[11px] font-bold bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/40";
    statusEl.textContent = "ONLINE (Simulating ESP32)";
    statusEl.className = "text-emerald-400 font-bold";
  } else {
    btn.textContent = "Start Node";
    btn.className = "px-2.5 py-1 rounded text-[11px] font-bold bg-pink-600/20 hover:bg-pink-600/30 text-pink-300 border border-pink-500/40";
    statusEl.textContent = "STOPPED";
    statusEl.className = "text-slate-500";
  }

  if (relayEl) {
    relayEl.textContent = data.relay;
    relayEl.className = data.relay === "ON" ? "text-emerald-400 font-bold" : "text-rose-400";
  }
  if (sensorEl) {
    sensorEl.textContent = `Temp: ${data.temperature} °C | Hum: ${data.humidity} %`;
  }
}

