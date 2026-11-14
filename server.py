import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.config import (
    BASE_DIR,
    SANDBOX_DIR,
    TEMPLATES_DIR,
    STATIC_DIR,
    ROUTER_BASE_URL,
    DEFAULT_MODEL,
    save_config
)
from core.agent import SuperAgent
from core.vscode_bridge import is_vscode_running, open_file_in_vscode, get_vscode_integration_info
from tools.local_tools import get_system_metrics, list_directory, read_file
from tools.iot_tools import serial_scan_ports, mqtt_publish
from tools.virtual_esp32 import virtual_esp32
from core.skills import SkillManager
from core.scheduler import TaskScheduler
from core.security import redact_object, redact_sensitive

app = FastAPI(title="Super Agent Neural Dashboard", version="2.0.0")

# Enable CORS for local VS Code webviews and external previews
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Shared singletons
agent = SuperAgent()
skill_manager = SkillManager()
scheduler = TaskScheduler(agent_instance=agent)

# Request schemas
class ChatRequest(BaseModel):
    prompt: str
    images: Optional[List[str]] = None
    model: Optional[str] = None

class ModelSelectRequest(BaseModel):
    model: str

class VSCodeOpenRequest(BaseModel):
    filepath: str
    line: Optional[int] = 1

class MqttPublishRequest(BaseModel):
    topic: str
    payload: str

@app.get("/", response_class=HTMLResponse)
async def index():
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        return HTMLResponse("<h1>Super Agent Dashboard loading...</h1>")
    with open(index_file, "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """Server-Sent Events (SSE) streaming endpoint for live ReAct loop, thought traces, and DAG updates."""
    prompt = req.prompt.strip()
    images = req.images or []
    if not prompt and not images:
        raise HTTPException(status_code=400, detail="Prompt or image cannot be empty.")

    if req.model:
        agent.update_model(req.model)

    async def event_generator():
        try:
            async for event in agent.run_stream(prompt, images=images):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            err_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(err_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/chat/reset")
async def chat_reset():
    agent.reset_conversation()
    return {"status": "success", "message": "Conversation history and artifacts reset."}

@app.get("/api/router/status")
async def router_status():
    """Returns 9Router connection health, latency, active model, and model list."""
    status = agent.client.check_connection()
    models = agent.client.list_models()
    return {
        "status": status,
        "active_model": agent.client.current_model,
        "models": models,
        "base_url": agent.client.base_url
    }

@app.post("/api/router/set-model")
async def set_model(req: ModelSelectRequest):
    agent.update_model(req.model)
    save_config("DEFAULT_MODEL", req.model)
    return {"status": "success", "active_model": req.model}

@app.get("/api/system/telemetry")
async def system_telemetry():
    """Real-time laptop hardware metrics."""
    metrics_str = get_system_metrics()
    return json.loads(metrics_str)

@app.get("/api/sandbox/files")
async def sandbox_files():
    """Lists files inside the sandbox directory."""
    files_str = list_directory("", recursive=True, max_items=100)
    return json.loads(files_str)

@app.get("/api/sandbox/file")
async def get_sandbox_file(path: str):
    """Reads content of a file in the sandbox."""
    res = read_file(path)
    return json.loads(res)

@app.get("/api/sandbox/preview/{filename:path}")
async def preview_sandbox_file(filename: str):
    """Directly serves an artifact file for live browser iframe preview (e.g. HTML, SVG)."""
    target = SANDBOX_DIR / filename
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(target))

@app.post("/api/vscode/open")
async def open_vscode(req: VSCodeOpenRequest):
    """Opens a file inside VS Code."""
    res = open_file_in_vscode(req.filepath, req.line)
    return res

@app.get("/api/vscode/status")
async def vscode_status():
    return get_vscode_integration_info()

@app.get("/api/iot/scan-serial")
async def iot_scan_serial():
    ports_str = serial_scan_ports()
    return json.loads(ports_str)

@app.post("/api/iot/mqtt")
async def iot_mqtt(req: MqttPublishRequest):
    res_str = mqtt_publish(req.topic, req.payload)
    return json.loads(res_str)

@app.get("/api/skills")
async def get_skills():
    """Returns all declarative skills discovered in skills/ directory."""
    return skill_manager.list_skills()

@app.get("/api/scheduler/tasks")
async def get_scheduled_tasks():
    return scheduler.list_tasks()

class TaskToggleRequest(BaseModel):
    task_id: str
    enabled: bool

@app.post("/api/scheduler/toggle")
async def toggle_scheduled_task(req: TaskToggleRequest):
    scheduler.toggle_task(req.task_id, req.enabled)
    return {"status": "success", "task_id": req.task_id, "enabled": req.enabled}

@app.get("/api/simulator/esp32/status")
async def simulator_status():
    return virtual_esp32.get_state()

@app.post("/api/simulator/esp32/toggle")
async def simulator_toggle():
    if virtual_esp32.is_running:
        virtual_esp32.stop()
    else:
        virtual_esp32.start()
    return virtual_esp32.get_state()

if __name__ == "__main__":
    import uvicorn
    from core.config import SERVER_HOST, SERVER_PORT
    uvicorn.run("server:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)
