import os
import sys

# Force UTF-8 encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
import webbrowser
import uvicorn
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.config import (
    SERVER_HOST,
    SERVER_PORT,
    ROUTER_BASE_URL,
    ROUTER_API_KEY,
    DEFAULT_MODEL
)
from core.llm_client import NineRouterClient
from core.vscode_bridge import is_vscode_running

console = Console()

def print_banner():
    # Print cool ASCII / rich banner
    banner_text = Text()
    banner_text.append("⚡ SUPER AGENT // NEURAL MATRIX ⚡\n", style="bold cyan")
    banner_text.append("Autonomous AI Agent connected to VS Code, 9Router, Internet & Local Laptop\n\n", style="italic white")
    
    # Table of connection status
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Komponen", style="cyan", width=22)
    table.add_column("Status / Endpoint", style="green")
    table.add_column("Keterangan", style="dim")

    # 1. 9Router
    client = NineRouterClient()
    conn = client.check_connection()
    if conn["online"]:
        table.add_row("🧠 9Router Gateway", f"[bold green]ONLINE[/bold green] ({conn['latency_ms']} ms)", f"{conn['models_count']} Model tersedia ({client.current_model})")
    else:
        table.add_row("🧠 9Router Gateway", "[bold yellow]STANDBY[/bold yellow]", f"Endpoint: {ROUTER_BASE_URL}")

    # 2. VS Code
    vscode_active = is_vscode_running()
    table.add_row("💻 VS Code Integration", "[bold green]TERHUBUNG[/bold green]" if vscode_active else "[yellow]STANDBY[/yellow]", "Workspace: d:\\super agent")

    # 3. Web Dashboard
    url = f"http://{SERVER_HOST}:{SERVER_PORT}"
    table.add_row("🌐 Neural Dashboard", f"[bold cyan]{url}[/bold cyan]", "Interactive DAG & Live Preview")

    console.print(Panel(banner_text, border_style="cyan"))
    console.print(table)
    console.print(f"\n[bold green]✓ Server sedang berjalan di: [link={url}]{url}[/link][/bold green]")
    console.print("[dim]Tekan Ctrl+C untuk menghentikan server.[/dim]\n")

    # Automatically launch browser
    try:
        webbrowser.open(url)
    except Exception:
        pass

def main():
    print_banner()
    uvicorn.run("server:app", host=SERVER_HOST, port=SERVER_PORT, reload=False, log_level="warning")

if __name__ == "__main__":
    main()
