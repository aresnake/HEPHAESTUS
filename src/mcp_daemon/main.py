"""MCP daemon bridging stdio transport to Blender HTTP provider."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from urllib import request


SRC_DIR = Path(__file__).resolve().parents[1]
if SRC_DIR and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

DEFAULT_URL = "http://127.0.0.1:8765/mcp"
ToolExecutor = Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]]


def _invalid_json_response() -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": "INVALID_REQUEST", "message": "invalid json"},
    }


def _write_response(response: Dict[str, Any]) -> None:
    try:
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    except Exception:  # noqa: BLE001
        return


def handle_stdio_payload(
    payload: Any,
    tool_executor: ToolExecutor = None,
    tool_lister: Optional[Callable[[], list]] = None,
) -> Dict[str, Any]:
    from mcp_core.server import handle_request

    if not isinstance(payload, dict):
        return _invalid_json_response()

    return handle_request(payload, tool_executor=tool_executor, tool_lister=tool_lister)


def run_stdio_with_initialize(
    tool_executor: ToolExecutor = None, tool_lister: Optional[Callable[[], list]] = None
) -> None:
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:  # noqa: BLE001
                response = _invalid_json_response()
            else:
                response = handle_stdio_payload(
                    payload,
                    tool_executor=tool_executor,
                    tool_lister=tool_lister,
                )

            _write_response(response)
    except Exception:  # noqa: BLE001
        return


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Proxy tools/call to Blender HTTP provider."""
    url = os.getenv("BLENDER_MCP_HTTP_URL", DEFAULT_URL)
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
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
        from blender_tools import list_tools

        run_stdio_with_initialize(tool_executor=execute_tool, tool_lister=list_tools)
    except KeyboardInterrupt:
        return
    except Exception as exc:  # noqa: BLE001
        try:
            sys.stderr.write(f"daemon error: {exc}\n")
        except Exception:
            pass


if __name__ == "__main__":
    main()
