import time
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ScheduledTask(BaseModel):
    id: str
    title: str
    prompt: str
    interval_seconds: int = 60
    enabled: bool = True
    last_run: Optional[float] = None
    last_status: Optional[str] = "pending"
    last_output: Optional[str] = None

class TaskScheduler:
    def __init__(self, agent_instance=None):
        self.tasks: Dict[str, ScheduledTask] = {
            "task_telemetry": ScheduledTask(
                id="task_telemetry",
                title="Laptop Health Audit",
                prompt="Cek kondisi CPU dan RAM laptop lalu buat catatan log singkat jika ada keanehan",
                interval_seconds=300,
                enabled=False
            ),
            "task_crypto": ScheduledTask(
                id="task_crypto",
                title="Crypto BTC/ETH Watcher",
                prompt="Cek harga terbaru Bitcoin dan Ethereum di internet dan simpan ke crypto_rates.json",
                interval_seconds=600,
                enabled=False
            )
        }
        self.agent = agent_instance
        self.running = False
        self._loop_task = None

    def list_tasks(self) -> List[Dict[str, Any]]:
        return [t.model_dump() for t in self.tasks.values()]

    def toggle_task(self, task_id: str, enabled: bool):
        if task_id in self.tasks:
            self.tasks[task_id].enabled = enabled

    def add_task(self, title: str, prompt: str, interval_sec: int) -> ScheduledTask:
        task_id = f"task_{int(time.time())}"
        task = ScheduledTask(
            id=task_id,
            title=title,
            prompt=prompt,
            interval_seconds=interval_sec,
            enabled=True
        )
        self.tasks[task_id] = task
        return task
