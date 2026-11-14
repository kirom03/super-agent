import json
from typing import Dict, Any, List, Callable

from tools.internet_tools import (
    search_web,
    fetch_web_page,
    call_rest_api,
    download_file,
    open_in_browser
)
from tools.local_tools import (
    get_system_metrics,
    write_file,
    read_file,
    edit_file_replace,
    list_directory,
    execute_terminal_command,
    execute_python_code
)
from tools.iot_tools import (
    serial_scan_ports,
    mqtt_publish,
    mqtt_read_telemetry
)
from core.vscode_bridge import open_file_in_vscode

# Function registry mapping
TOOL_MAPPING: Dict[str, Callable] = {
    "search_web": search_web,
    "fetch_web_page": fetch_web_page,
    "call_rest_api": call_rest_api,
    "download_file": download_file,
    "get_system_metrics": get_system_metrics,
    "write_file": write_file,
    "read_file": read_file,
    "edit_file_replace": edit_file_replace,
    "list_directory": list_directory,
    "execute_terminal_command": execute_terminal_command,
    "execute_python_code": execute_python_code,
    "open_file_in_vscode": open_file_in_vscode,
    "serial_scan_ports": serial_scan_ports,
    "mqtt_publish": mqtt_publish,
    "mqtt_read_telemetry": mqtt_read_telemetry,
    "open_in_browser": open_in_browser,
}

# Metadata categories for DAG visualization
TOOL_CATEGORIES: Dict[str, str] = {
    "search_web": "internet",
    "fetch_web_page": "internet",
    "call_rest_api": "internet",
    "download_file": "internet",
    "open_in_browser": "internet",
    "get_system_metrics": "local_system",
    "write_file": "local_file",
    "read_file": "local_file",
    "edit_file_replace": "local_file",
    "list_directory": "local_file",
    "execute_terminal_command": "terminal",
    "execute_python_code": "python",
    "open_file_in_vscode": "vscode",
    "serial_scan_ports": "iot",
    "mqtt_publish": "iot",
    "mqtt_read_telemetry": "iot"
}

TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Searches the live internet for documents, APIs, solutions, tutorials, libraries, and real-time facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Specific search query."
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of search results to return (default 5).",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_web_page",
            "description": "Fetches a URL from the internet and returns its clean, readable text/markdown content without ads or scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The full HTTP/HTTPS URL to fetch."
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return (default 6000).",
                        "default": 6000
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_rest_api",
            "description": "Executes an HTTP REST API call (GET, POST, PUT, DELETE) and returns status code, response headers, and body.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The API endpoint URL."},
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"], "default": "GET"},
                    "headers": {"type": "object", "description": "Optional HTTP request headers."},
                    "json_body": {"type": "object", "description": "Optional JSON payload for POST/PUT requests."}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_file",
            "description": "Downloads an online file or asset directly into the local sandbox directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The online file URL."},
                    "filename": {"type": "string", "description": "Local destination filename inside sandbox."}
                },
                "required": ["url", "filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_in_browser",
            "description": "Opens a web URL or local file URL directly in the user's laptop web browser (Chrome, Edge, etc.).",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The web URL to open, e.g. 'https://github.com' or 'http://localhost:7860'."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_metrics",
            "description": "Reads real-time laptop telemetry: CPU load %, RAM usage, Disk space on C: and D:, battery level, and top processes.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Creates or overwrites a file on the local laptop with code, markdown, configurations, or scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file (relative to sandbox/ or absolute path)."
                    },
                    "content": {
                        "type": "string",
                        "description": "The full code or text content to write."
                    }
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Reads the content of a file from the local laptop.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to file (relative to sandbox/ or absolute path)."
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file_replace",
            "description": "Performs exact string search and replace inside an existing local file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Path to file."},
                    "old_text": {"type": "string", "description": "Exact text to find and replace."},
                    "new_text": {"type": "string", "description": "New replacement text."}
                },
                "required": ["filepath", "old_text", "new_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lists files and subdirectories in a local directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dirpath": {
                        "type": "string",
                        "description": "Folder path (defaults to sandbox)."
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Whether to list recursively.",
                        "default": False
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_terminal_command",
            "description": "Executes a PowerShell terminal command on the local laptop. Use for running git, npm, pip, builds, tests, or system utilities.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The PowerShell command to run."
                    },
                    "working_dir": {
                        "type": "string",
                        "description": "Optional directory to run in. Defaults to sandbox."
                    }
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python_code",
            "description": "Runs dynamic Python code inside the sandbox environment and returns stdout and stderr.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Python code block to execute."
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_file_in_vscode",
            "description": "Opens a generated or edited file directly inside the user's active VS Code editor window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path of the file to open."
                    },
                    "line": {
                        "type": "integer",
                        "description": "Line number to focus on."
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "serial_scan_ports",
            "description": "Scans laptop USB serial COM ports to discover connected microcontrollers (ESP32, Arduino, Pico).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mqtt_publish",
            "description": "Sends an MQTT message payload to an IoT smart device topic (relays, lights, motors).",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "MQTT topic (e.g. home/living/light)."},
                    "payload": {"type": "string", "description": "Payload text or command (e.g. ON/OFF/JSON)."}
                },
                "required": ["topic", "payload"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mqtt_read_telemetry",
            "description": "Listens for telemetry sensor data published to an MQTT topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "MQTT topic to monitor."},
                    "timeout_sec": {"type": "integer", "description": "Seconds to wait for message (default 5).", "default": 5}
                },
                "required": ["topic"]
            }
        }
    }
]

def dispatch_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Dispatches a tool call safely and returns the stringified result."""
    func = TOOL_MAPPING.get(tool_name)
    if not func:
        return json.dumps({"status": "error", "error": f"Tool '{tool_name}' is not registered."})

    try:
        res = func(**arguments)
        if isinstance(res, str):
            return res
        return json.dumps(res, indent=2, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "tool": tool_name, "error": str(e)})
