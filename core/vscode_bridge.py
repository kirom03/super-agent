import os
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import psutil
from core.config import BASE_DIR, SANDBOX_DIR

def is_vscode_running() -> bool:
    """Checks if VS Code (Code.exe) process is actively running on this laptop."""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() in ['code.exe', 'code']:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def open_file_in_vscode(filepath: str, line: Optional[int] = None) -> Dict[str, Any]:
    """Instructs VS Code to open a file at an optional line number."""
    target = Path(filepath)
    if not target.is_absolute():
        # Check sandbox first, then project root
        sb_target = SANDBOX_DIR / target
        if sb_target.exists():
            target = sb_target
        else:
            base_target = BASE_DIR / target
            if base_target.exists():
                target = base_target
            else:
                target = sb_target

    if not target.exists():
        return {"status": "error", "error": f"File '{target}' does not exist."}

    # Use 'cmd.exe /c code' or direct code.cmd to ensure Windows resolves it properly
    code_bin = "code.cmd" if os.name == "nt" else "code"
    cmd = [code_bin, "-g", f"{str(target)}:{line or 1}"]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=10, shell=(os.name == "nt"))
        return {"status": "success", "filepath": str(target), "message": "Opened in VS Code."}
    except Exception as e:
        return {"status": "error", "filepath": str(target), "error": str(e)}

def get_vscode_integration_info() -> Dict[str, Any]:
    """Returns status and configuration details for VS Code integration."""
    running = is_vscode_running()
    tasks_file = BASE_DIR / ".vscode" / "tasks.json"
    
    return {
        "status": "ready",
        "vscode_running": running,
        "workspace_root": str(BASE_DIR),
        "tasks_configured": tasks_file.exists(),
        "sandbox_path": str(SANDBOX_DIR),
        "mcp_enabled": True
    }
