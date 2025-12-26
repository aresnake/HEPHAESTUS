"""MCP daemon bridging stdio transport to Blender HTTP provider."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict
from urllib import request


SRC_DIR = Path(__file__).resolve().parents[1]
if SRC_DIR and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DEFAULT_URL = "http://127.0.0.1:8765/mcp"


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Proxy tools.call to Blender HTTP provider."""
    url = os.getenv("BLENDER_MCP_HTTP_URL", DEFAULT_URL)
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools.call",
        "params": {"tool": tool_name, "arguments": arguments or {}},
    }

    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"http error: {exc}") from exc

    try:
        response = json.loads(body)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("invalid json response") from exc

    if isinstance(response, dict) and "result" in response:
        result = response.get("result")
        if isinstance(result, dict):
            return result
        raise RuntimeError("invalid result shape")

    if isinstance(response, dict) and "error" in response:
        error = response.get("error") or {}
        code = error.get("code")
        message = error.get("message")
        raise RuntimeError(f"{code}: {message}")

    raise RuntimeError("invalid response")


def main() -> None:
    try:
        from mcp_core.transport_stdio import run_stdio

        run_stdio(tool_executor=execute_tool)
    except Exception as exc:  # noqa: BLE001
        try:
            sys.stderr.write(f"daemon error: {exc}\n")
        except Exception:
            pass


if __name__ == "__main__":
    main()
