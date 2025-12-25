import sys
import json
import traceback
from typing import Any, Dict, List

from app.tools.vietcap_tools import VIETCAP_TOOLS

def get_tool_schema(func) -> Dict[str, Any]:
    """
    Very basic schema generation from function signature and docstring.
    """
    import inspect

    sig = inspect.signature(func)
    doc = func.__doc__ or ""

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name == "self": continue

        # Simple type mapping
        p_type = "string"
        if param.annotation == int:
            p_type = "number"
        elif param.annotation == bool:
            p_type = "boolean"
        elif param.annotation == List[str] or param.annotation == list:
            p_type = "array"

        properties[name] = {
            "type": p_type,
            "description": f"Parameter {name}"
        }

        if param.default == inspect.Parameter.empty:
            required.append(name)

    return {
        "name": func.__name__,
        "description": doc.strip().split("\n")[0],
        "inputSchema": {
            "type": "object",
            "properties": properties,
            "required": required
        }
    }

def main():
    """
    Minimal MCP Server implementation following JSON-RPC 2.0 over stdio.
    """
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            # MCP sends JSON-RPC lines
            request = json.loads(line)
            req_id = request.get("id")
            method = request.get("method")
            params = request.get("params", {})

            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "stock-agent-tools",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "notifications/initialized":
                continue # No response needed
            elif method == "tools/list":
                tools = [get_tool_schema(t) for t in VIETCAP_TOOLS]
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": tools
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})

                result = {"error": f"Tool {tool_name} not found"}
                for tool in VIETCAP_TOOLS:
                    if tool.__name__ == tool_name:
                        try:
                            res = tool(**tool_args)
                            result = {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}]}
                        except Exception as e:
                            result = {"isError": True, "content": [{"type": "text", "text": str(e)}]}
                        break

                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": result
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method {method} not found"
                    }
                }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except Exception as e:
            pass

if __name__ == "__main__":
    main()
