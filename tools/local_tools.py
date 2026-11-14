import os
import sys
import json
import subprocess
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from core.config import BASE_DIR, SANDBOX_DIR, COMMAND_TIMEOUT_SECONDS

def get_system_metrics() -> str:
    """Returns real-time laptop telemetry: CPU, RAM, Disk, Battery, and top processes."""
    try:
        cpu_usage = psutil.cpu_percent(interval=0.1)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_freq = psutil.cpu_freq()
        
        mem = psutil.virtual_memory()
        ram_total_gb = round(mem.total / (1024 ** 3), 2)
        ram_used_gb = round(mem.used / (1024 ** 3), 2)
        ram_available_gb = round(mem.available / (1024 ** 3), 2)
        ram_percent = mem.percent

        # Disks (C: and D: if available)
        disks = []
        for partition in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 2),
                    "free_gb": round(usage.free / (1024 ** 3), 2),
                    "used_percent": usage.percent
                })
            except Exception:
                pass

        # Battery
        battery_info = {}
        battery = psutil.sensors_battery()
        if battery:
            battery_info = {
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "charging": battery.power_plugged
            }
        else:
            battery_info = {"status": "AC Desktop or battery sensor unavailable"}

        # Top 5 processes by memory
        top_processes = []
        for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                            key=lambda p: p.info['memory_percent'] or 0, reverse=True)[:5]:
            try:
                top_processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cpu_percent": proc.info['cpu_percent'],
                    "memory_percent": round(proc.info['memory_percent'] or 0, 1)
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        return json.dumps({
            "status": "success",
            "cpu": {
                "usage_percent": cpu_usage,
                "logical_cores": cpu_count_logical,
                "physical_cores": cpu_count_physical,
                "current_freq_mhz": round(cpu_freq.current, 1) if cpu_freq else None
            },
            "ram": {
                "used_percent": ram_percent,
                "used_gb": ram_used_gb,
                "available_gb": ram_available_gb,
                "total_gb": ram_total_gb
            },
            "disks": disks,
            "battery": battery_info,
            "top_processes": top_processes
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})

def resolve_target_path(filepath: str) -> Path:
    """Safely resolves paths. If relative, checks if it exists in BASE_DIR first, otherwise defaults to SANDBOX_DIR."""
    p = Path(filepath)
    if p.is_absolute():
        return p
    # Check if exists in BASE_DIR
    base_candidate = BASE_DIR / p
    if base_candidate.exists():
        return base_candidate
    return SANDBOX_DIR / p

def write_file(filepath: str, content: str) -> str:
    """Creates or overwrites a file on the local laptop with specified content."""
    try:
        target = resolve_target_path(filepath)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)

        return json.dumps({
            "status": "success",
            "filepath": str(target),
            "bytes_written": len(content.encode("utf-8")),
            "filename": target.name
        })
    except Exception as e:
        return json.dumps({"status": "error", "filepath": filepath, "error": str(e)})

def read_file(filepath: str, max_chars: int = 12000) -> str:
    """Reads the content of a file on the local laptop."""
    try:
        target = resolve_target_path(filepath)
        if not target.exists():
            return json.dumps({"status": "error", "filepath": str(target), "error": "File does not exist."})
        if not target.is_file():
            return json.dumps({"status": "error", "filepath": str(target), "error": "Target is a directory, not a file."})

        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        truncated = False
        if len(content) > max_chars:
            content = content[:max_chars]
            truncated = True

        return json.dumps({
            "status": "success",
            "filepath": str(target),
            "filename": target.name,
            "truncated": truncated,
            "length": len(content),
            "content": content
        })
    except Exception as e:
        return json.dumps({"status": "error", "filepath": filepath, "error": str(e)})

def edit_file_replace(filepath: str, old_text: str, new_text: str) -> str:
    """Replaces exact target text inside an existing file."""
    try:
        target = resolve_target_path(filepath)
        if not target.exists():
            return json.dumps({"status": "error", "filepath": str(target), "error": "File not found."})

        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        if old_text not in content:
            return json.dumps({"status": "error", "error": "Target string not found in file. Ensure exact match."})

        new_content = content.replace(old_text, new_text, 1)
        with open(target, "w", encoding="utf-8", errors="replace") as f:
            f.write(new_content)

        return json.dumps({"status": "success", "filepath": str(target), "message": "Text replaced successfully."})
    except Exception as e:
        return json.dumps({"status": "error", "filepath": filepath, "error": str(e)})

def list_directory(dirpath: str = "", recursive: bool = False, max_items: int = 60) -> str:
    """Lists files and directories inside a local folder."""
    try:
        target = Path(dirpath) if dirpath and Path(dirpath).is_absolute() else (SANDBOX_DIR / dirpath if dirpath else SANDBOX_DIR)
        if not target.exists():
            return json.dumps({"status": "error", "error": f"Path '{target}' does not exist."})

        items = []
        pattern = "**/*" if recursive else "*"
        count = 0
        for entry in target.glob(pattern):
            if count >= max_items:
                break
            try:
                rel = entry.relative_to(target)
                is_dir = entry.is_dir()
                size = entry.stat().st_size if not is_dir else 0
                items.append({
                    "name": entry.name,
                    "relative_path": str(rel),
                    "is_directory": is_dir,
                    "size_bytes": size
                })
                count += 1
            except Exception:
                pass

        return json.dumps({
            "status": "success",
            "directory": str(target),
            "count": len(items),
            "items": items
        }, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "dirpath": dirpath, "error": str(e)})

def execute_terminal_command(command: str, working_dir: Optional[str] = None, timeout_sec: int = COMMAND_TIMEOUT_SECONDS) -> str:
    """Executes a PowerShell shell command on the local laptop and returns stdout, stderr, and exit code."""
    try:
        cwd = Path(working_dir) if working_dir and Path(working_dir).is_absolute() else SANDBOX_DIR
        cwd.mkdir(parents=True, exist_ok=True)

        proc = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            encoding="utf-8",
            errors="replace"
        )

        return json.dumps({
            "status": "completed",
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "working_dir": str(cwd)
        }, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return json.dumps({
            "status": "timeout",
            "error": f"Command timed out after {timeout_sec} seconds."
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "error": str(e)
        })

def execute_python_code(code: str) -> str:
    """Runs a Python script dynamically in the sandbox environment and captures output."""
    temp_script = SANDBOX_DIR / "_exec_tmp.py"
    try:
        with open(temp_script, "w", encoding="utf-8") as f:
            f.write(code)

        proc = subprocess.run(
            [sys.executable, str(temp_script)],
            cwd=str(SANDBOX_DIR),
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            encoding="utf-8",
            errors="replace"
        )
        
        return json.dumps({
            "status": "completed",
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip()
        }, ensure_ascii=False)
    except subprocess.TimeoutExpired:
        return json.dumps({"status": "timeout", "error": f"Python script timed out after {COMMAND_TIMEOUT_SECONDS}s."})
    except Exception as e:
        return json.dumps({"status": "error", "error": str(e)})
    finally:
        if temp_script.exists():
            try:
                temp_script.unlink()
            except Exception:
                pass
