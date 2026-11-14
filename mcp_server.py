"""
Super Agent Model Context Protocol (MCP) Server for VS Code.
Exposes Super Agent's Internet & Local Laptop tools directly to VS Code Copilot & Claude Code.
"""

import sys
import json
from typing import Dict, Any
from tools.registry import TOOL_DEFINITIONS, dispatch_tool

def handle_request(req: Dict[str, Any]) -> Dict[str, Any]:
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "super-agent-vscode-bridge",
                    "version": "2.0.0"
                }
            }
        }

    elif method == "tools/list":
        # Format tool definitions for MCP
        tools = []
        for defn in TOOL_DEFINITIONS:
            fn = defn["function"]
            tools.append({
                "name": fn["name"],
                "description": fn["description"],
                "inputSchema": fn["parameters"]
            })
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": tools}
        }

    elif method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})
        
        output_str = dispatch_tool(tool_name, args)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": output_str
                    }
                ]
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method '{method}' not found."}
    }

def main():
    """Stdio JSON-RPC loop for VS Code MCP client."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_request(req)
            sys.stdout.write(json.dumps(res) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
