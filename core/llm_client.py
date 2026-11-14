import os
import json
import httpx
from typing import List, Dict, Any, Generator, Optional
from openai import OpenAI
from core.config import ROUTER_BASE_URL, ROUTER_API_KEY, DEFAULT_MODEL, detect_9router_key

class NineRouterClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.base_url = (base_url or ROUTER_BASE_URL).rstrip("/")
        self.api_key = api_key or ROUTER_API_KEY or detect_9router_key() or "dummy"
        self.current_model = model or DEFAULT_MODEL
        self._init_client()

    def _init_client(self):
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=120.0
        )

    def update_settings(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        if base_url:
            self.base_url = base_url.rstrip("/")
        if api_key:
            self.api_key = api_key
        if model:
            self.current_model = model
        self._init_client()

    def check_connection(self) -> Dict[str, Any]:
        """Tests the connection to 9Router and measures ping latency."""
        import time
        t0 = time.time()
        try:
            with httpx.Client(timeout=4.0) as client:
                res = client.get(f"{self.base_url}/models", headers={"Authorization": f"Bearer {self.api_key}"})
                latency = round((time.time() - t0) * 1000, 1)
                if res.status_code == 200:
                    models = [m["id"] for m in res.json().get("data", [])]
                    return {
                        "online": True,
                        "base_url": self.base_url,
                        "latency_ms": latency,
                        "models_count": len(models),
                        "models": models,
                        "active_model": self.current_model
                    }
                else:
                    return {
                        "online": False,
                        "base_url": self.base_url,
                        "latency_ms": latency,
                        "error": f"HTTP {res.status_code}: {res.text[:100]}"
                    }
        except Exception as e:
            return {
                "online": False,
                "base_url": self.base_url,
                "latency_ms": -1,
                "error": str(e)
            }

    def list_models(self) -> List[Dict[str, Any]]:
        """Returns the list of all available models from 9Router."""
        try:
            res = self.client.models.list()
            return [
                {
                    "id": m.id,
                    "owned_by": getattr(m, "owned_by", "router"),
                    "context_length": getattr(m, "context_length", 128000)
                }
                for m in res.data
            ]
        except Exception:
            # Fallback list of known working models on 9Router
            return [
                {"id": "ag/gemini-3.8-flash-low", "owned_by": "ag", "context_length": 1048576},
                {"id": "ag/gemini-3.8-flash-high", "owned_by": "ag", "context_length": 1048576},
                {"id": "ag/claude-sonnet-4-6", "owned_by": "ag", "context_length": 1000000},
                {"id": "ag/claude-opus-4-6-thinking", "owned_by": "ag", "context_length": 200000},
                {"id": "ag/gpt-oss-120b-medium", "owned_by": "ag", "context_length": 128000},
                {"id": "free-combo", "owned_by": "combo", "context_length": 128000}
            ]

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        temperature: float = 0.2
    ):
        """Sends a standard chat completion request."""
        target_model = model or self.current_model
        kwargs = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        return self.client.chat.completions.create(**kwargs)
