import os
import sys
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
SANDBOX_DIR = BASE_DIR / "sandbox"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

# Load existing .env if present
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

def detect_9router_key() -> str:
    """Attempts to auto-discover an active 9Router API key from the local 9Router database."""
    # Check environment variable first
    env_key = os.getenv("NINEROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key

    # Check Windows AppData path for 9router data.sqlite
    appdata = os.getenv("APPDATA")
    if appdata:
        db_path = Path(appdata) / "9router" / "db" / "data.sqlite"
        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                c = conn.cursor()
                # Find active key (prefer vs-code or default key)
                row = c.execute("SELECT key FROM apiKeys WHERE isActive=1 ORDER BY createdAt DESC LIMIT 1").fetchone()
                conn.close()
                if row and row[0]:
                    return row[0]
            except Exception:
                pass
    return ""

# 9Router configuration
DEFAULT_ROUTER_URL = "http://localhost:20128/v1"
ROUTER_BASE_URL = os.getenv("NINEROUTER_BASE_URL", DEFAULT_ROUTER_URL)
ROUTER_API_KEY = detect_9router_key()
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "ag/gemini-3.8-flash-low")

# Super Agent Execution limits
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "25"))
COMMAND_TIMEOUT_SECONDS = int(os.getenv("COMMAND_TIMEOUT_SECONDS", "60"))

# Hardware / IoT configurations
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", "super_agent/laptop")
DEFAULT_SERIAL_BAUDRATE = int(os.getenv("DEFAULT_SERIAL_BAUDRATE", "115200"))

# Server configuration
SERVER_HOST = os.getenv("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("SERVER_PORT", "7860"))

def save_config(key: str, value: str):
    """Saves or updates a setting in the local .env file."""
    lines = []
    found = False
    
    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{key}="):
                    lines.append(f"{key}={value}\n")
                    found = True
                else:
                    lines.append(line)
                    
    if not found:
        lines.append(f"{key}={value}\n")
        
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)
    os.environ[key] = value
