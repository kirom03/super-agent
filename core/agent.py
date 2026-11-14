import os
import json
import time
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator

from core.config import MAX_AGENT_ITERATIONS, detect_9router_key
from core.prompts import SUPER_AGENT_SYSTEM_PROMPT
from core.llm_client import NineRouterClient
from tools.registry import TOOL_DEFINITIONS, dispatch_tool, TOOL_CATEGORIES

class SuperAgent:
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.client = NineRouterClient(base_url=base_url, api_key=api_key, model=model)
        self.conversation_history: List[Dict[str, Any]] = [
            {"role": "system", "content": SUPER_AGENT_SYSTEM_PROMPT}
        ]
        self.artifacts_created: List[str] = []

    def reset_conversation(self):
        """Clears the history while preserving the system prompt."""
        self.conversation_history = [
            {"role": "system", "content": SUPER_AGENT_SYSTEM_PROMPT}
        ]
        self.artifacts_created = []

    def update_model(self, model: str):
        self.client.current_model = model

    async def run_stream(
        self,
        user_prompt: str,
        images: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Runs the ReAct loop and streams real-time events for the frontend:
        - node_update: For the live neural execution DAG graph
        - thinking: Reasoning / thought trace
        - token: Response text
        - tool_call_start, tool_call_end
        - step_complete
        - done
        """
        if images and len(images) > 0:
            content_parts = []
            if user_prompt:
                content_parts.append({"type": "text", "text": user_prompt})
            for img in images:
                # img is data URL like "data:image/png;base64,..." or URL
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": img}
                })
            self.conversation_history.append({"role": "user", "content": content_parts})
        else:
            self.conversation_history.append({"role": "user", "content": user_prompt})

        # Emit initial goal node for the DAG graph
        yield {
            "type": "node_update",
            "node": {
                "id": "goal",
                "label": "User Goal",
                "status": "completed",
                "category": "user",
                "detail": user_prompt[:80] + ("..." if len(user_prompt) > 80 else "")
            }
        }

        iterations = 0
        while iterations < MAX_AGENT_ITERATIONS:
            iterations += 1
            step_id = f"step_{iterations}"
            
            # Emit router planning node
            yield {
                "type": "node_update",
                "node": {
                    "id": step_id,
                    "label": f"9Router Step {iterations}",
                    "status": "running",
                    "category": "router",
                    "detail": f"Model: {self.client.current_model}"
                }
            }

            yield {
                "type": "thinking_start",
                "step": iterations,
                "message": f"9Router ({self.client.current_model}) sedang merencanakan & berpikir..."
            }

            t0 = time.time()
            try:
                # Call 9Router in a threadpool so it doesn't block the async event loop
                response = await asyncio.to_thread(
                    self.client.chat_completion,
                    messages=self.conversation_history,
                    tools=TOOL_DEFINITIONS,
                    model=self.client.current_model
                )
            except Exception as e:
                err_msg = f"9Router API Error: {str(e)}"
                yield {
                    "type": "node_update",
                    "node": {"id": step_id, "status": "error", "error": err_msg}
                }
                yield {"type": "error", "message": err_msg}
                return

            choice = response.choices[0]
            message = choice.message
            elapsed_sec = round(time.time() - t0, 2)

            self.conversation_history.append(message)

            # Check for DeepSeek R1 / Claude thinking content
            reasoning = getattr(message, "reasoning_content", None)
            if reasoning:
                yield {
                    "type": "thinking_content",
                    "step": iterations,
                    "content": reasoning
                }

            # Check if tools are requested
            tool_calls = getattr(message, "tool_calls", None)

            if not tool_calls:
                # No more tools called; Task is complete!
                final_text = message.content or "Tugas selesai dieksekusi."
                yield {
                    "type": "node_update",
                    "node": {
                        "id": step_id,
                        "status": "completed",
                        "latency_sec": elapsed_sec,
                        "detail": "Final synthesis complete"
                    }
                }
                yield {
                    "type": "token",
                    "content": final_text
                }
                yield {
                    "type": "done",
                    "step": iterations,
                    "total_iterations": iterations,
                    "model": self.client.current_model,
                    "latency_sec": elapsed_sec
                }
                return

            # Complete router step node
            yield {
                "type": "node_update",
                "node": {
                    "id": step_id,
                    "status": "completed",
                    "latency_sec": elapsed_sec,
                    "detail": f"Calling {len(tool_calls)} tool(s)"
                }
            }

            # Execute tool calls
            for idx, tool_call in enumerate(tool_calls):
                tool_name = tool_call.function.name
                tool_id = tool_call.id
                raw_args = tool_call.function.arguments
                
                try:
                    tool_args = json.loads(raw_args)
                except Exception:
                    tool_args = {}

                tool_node_id = f"tool_{iterations}_{idx}_{tool_name}"
                category = TOOL_CATEGORIES.get(tool_name, "general")

                # Emit tool node running
                yield {
                    "type": "node_update",
                    "node": {
                        "id": tool_node_id,
                        "parent_id": step_id,
                        "label": tool_name,
                        "category": category,
                        "status": "running",
                        "args": tool_args
                    }
                }

                yield {
                    "type": "tool_start",
                    "step": iterations,
                    "tool_name": tool_name,
                    "args": tool_args,
                    "category": category
                }

                # Track generated files
                if tool_name == "write_file" and "filepath" in tool_args:
                    self.artifacts_created.append(tool_args["filepath"])

                # Dispatch tool call safely in threadpool
                tool_t0 = time.time()
                tool_output_str = await asyncio.to_thread(dispatch_tool, tool_name, tool_args)
                tool_latency = round((time.time() - tool_t0) * 1000, 1)

                is_error = '"status": "error"' in tool_output_str or '"error":' in tool_output_str

                # Emit tool node complete
                yield {
                    "type": "node_update",
                    "node": {
                        "id": tool_node_id,
                        "status": "error" if is_error else "completed",
                        "latency_ms": tool_latency,
                        "output_preview": tool_output_str[:250] + ("..." if len(tool_output_str) > 250 else "")
                    }
                }

                yield {
                    "type": "tool_end",
                    "step": iterations,
                    "tool_name": tool_name,
                    "output": tool_output_str,
                    "latency_ms": tool_latency,
                    "status": "error" if is_error else "success"
                }

                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "content": tool_output_str
                })

        yield {
            "type": "done",
            "message": "⚠️ Batas maksimum iterasi ReAct tercapai.",
            "step": iterations
        }
