# ⚡ Super Agent — Autonomous Neural System & Visual Matrix

**Super Agent** adalah sistem AI Agent otonom generasi berikutnya yang berjalan langsung di laptop Anda, terhubung erat dengan **VS Code**, ditenagai oleh **9Router**, dan memiliki akses penuh terhadap kemampuan **Internet (Live Web Search & Scrape)** serta **Sistem Lokal Laptop (PowerShell, File System, Python REPL, Hardware Telemetry, dan IoT Actuator)**.

Dibangun dengan visualisasi canggih (*Interactive Neural DAG Graph, Real-Time Token Streaming, Live Sandbox Web App Previewer, dan Hardware Telemetry HUD*) yang dirancang **jauh lebih kaya, interaktif, dan futuristik dibandingkan Muse AI**.

---

## 🌟 Perbandingan Super Agent vs Muse AI

| Fitur | Muse AI | ⚡ Super Agent (Pro Matrix) |
|---|---|---|
| **Konektivitas Router** | DeepSeek direct API saja | **9Router Universal Gateway** (`http://localhost:20128/v1`) + Auto Model Switching (Claude Sonnet 4.6, Claude Opus Thinking, Gemini 3.8 Flash, dll.) |
| **Visualisasi Workflow** | Hanya chat teks statis & JSON raw | **Interactive Neural DAG Execution Graph** (visualisasi alur berpikir AI node-by-node real-time dengan SVG animasi) |
| **Streaming Output** | Menunggu 30 detik sampai selesai baru muncul | **Server-Sent Events (SSE) Real-Time Token Streaming** + Drawer *Reasoning & Deep Thinking* (mirip Claude Thinking & DeepSeek R1) |
| **Live Web App Preview** | Tidak ada | **Interactive Sandbox Iframe** (Aplikasi HTML/CSS/JS yang dibuat agen langsung bisa dijalankan & diuji di browser tanpa buka tab baru) |
| **Integrasi VS Code** | Manual | **1-Click Launch Tasks**, Bridge `code --goto`, dan **Model Context Protocol (MCP)** server siap pakai |
| **Hardware Telemetry** | Tidak ada | **Real-Time Live HUD** (CPU Load %, RAM Allocator, Partisi Disk C: & D: Free GB, Status Baterai, Top Process) |
| **Alat Internet** | Web search basic | **DDGS Live Search, Clean Web Scraper, REST API Caller, Direct File Downloader** |
| **Alat Laptop Lokal** | Basic terminal | **PowerShell Async, File Manager (Read/Write/Edit Replace), Python Dynamic REPL, USB Serial Scan, MQTT IoT** |

---

## 🏗️ Arsitektur Sistem

```text
d:\super agent/
├── core/
│   ├── config.py              # Konfigurasi & auto-detect API key 9Router dari SQLite
│   ├── llm_client.py          # Klien 9Router OpenAI-compatible dengan latency monitor
│   ├── agent.py               # ReAct Autonomous Engine dengan SSE streaming & DAG node events
│   ├── prompts.py             # Prompt otonom spesialisasi Internet + Local System
│   └── vscode_bridge.py       # Jembatan sinkronisasi dengan VS Code editor
├── tools/
│   ├── internet_tools.py      # DDGS Live Search, Web Scraper, REST API, Downloader
│   ├── local_tools.py         # Hardware telemetry (psutil), Terminal PowerShell, File Manager, Python REPL
│   ├── iot_tools.py           # USB Serial COM scan (ESP32/Arduino) & MQTT Smart Home
│   └── registry.py            # Registry function calling & metadata kategori visual
├── static/
│   ├── css/dashboard.css      # Cyberpunk glassmorphism, neon glowing & DAG styles
│   └── js/
│       ├── app.js             # SSE stream handler, model switcher, telemetry polling
│       └── dag_renderer.js    # Interactive Neural Execution Graph (Canvas/SVG)
├── templates/
│   └── index.html             # Next-Gen Dashboard (3-Column Tactical Cyber Layout)
├── sandbox/                   # Lingkungan kerja aman untuk file proyek yang dibuat agen
├── .vscode/
│   └── tasks.json             # Task VS Code untuk menjalankan Super Agent dengan 1 klik
├── server.py                  # Backend FastAPI dengan SSE, REST API, dan File Preview
├── run.py                     # Entry point dengan Rich terminal banner & auto browser launch
├── mcp_server.py              # Model Context Protocol Server untuk Copilot / Cline
├── requirements.txt           # Dependensi Python
└── README.md                  # Dokumentasi lengkap
```

---

## ⚡ Cara Menjalankan

### Cara 1: Langsung dari VS Code (Paling Mudah)
1. Buka folder `d:\super agent` di VS Code.
2. Tekan `Ctrl + Shift + B` (atau buka menu **Terminal -> Run Task -> Launch Super Agent Dashboard**).
3. Browser akan otomatis terbuka menampilkan dashboard di `http://localhost:7860`.

### Cara 2: Melalui Terminal / PowerShell
Buka PowerShell di folder `d:\super agent`:
```powershell
python run.py
```
Super Agent akan memverifikasi koneksi 9Router pada port `20128`, menampilkan banner telemetri di terminal, dan membuka browser secara otomatis.

---

## 🧠 Integrasi 9Router

Super Agent secara otomatis mendeteksi server **9Router** yang berjalan di laptop Anda (`http://localhost:20128/v1`).
- API key yang tersimpan di database lokal 9Router (`%APPDATA%\9router\db\data.sqlite`) langsung dibaca secara otomatis tanpa perlu setup ulang.
- Anda dapat mengganti model AI secara instan langsung dari dropdown di header Dashboard:
  - `ag/gemini-3.8-flash-low` (Sangat cepat untuk tugas instan & alat)
  - `ag/gemini-3.8-flash-high` (Respon cerdas, penalaran tinggi)
  - `ag/claude-sonnet-4-6` (Arsitektur kode & analisa mendalam)
  - `ag/claude-opus-4-6-thinking` (Deep thinking / reasoning kompleks)
  - `free-combo`

---

## 💡 Contoh Skenario Penggunaan

### 1. Riset Web & Informasi Terkini (Internet)
> *"Cari dokumentasi dan library Python terbaru untuk memproses gambar dengan AI, lalu buatkan perbandingannya."*

### 2. Membuat Web App & Live Testing di Sandbox (Local + Web Preview)
> *"Buatkan aplikasi web pemutar audio synthesizer mini menggunakan Web Audio API dalam satu file HTML/JS/CSS di sandbox, lalu buka preview-nya."*
*(Aplikasi akan langsung muncul di panel **Live Preview** sebelah kanan dan siap dites interaktif!)*

### 3. Otomasi Laptop & Pemantauan Sistem (Local Laptop)
> *"Periksa beban CPU dan RAM laptop saya, lalu cari file log yang ukurannya lebih dari 10MB di folder Downloads."*

### 4. Eksekusi Script & Testing (Terminal & Python)
> *"Tulis script Python untuk menghitung matriks korelasi dan simpan hasilnya dalam bentuk file JSON di sandbox."*

### 5. Mikrokontroler & IoT (Physical Hardware)
> *"Scan apakah ada ESP32 atau Arduino yang dicolokkan ke port USB laptop ini, lalu buatkan program firmware Arduino C++ untuk membaca suhu DHT22."*

### 6. Integrasi VS Code
> *"Buka file yang baru saja dibuat ke dalam editor VS Code saya."*
*(Super Agent akan memanggil jembatan VS Code dan membuka file di jendela editor aktif Anda!)*
