"""Minimal stdio transport for MCP Core."""

import json
import sys
from typing import Any, Callable, Dict, Optional

from .server import handle_request


def _invalid_json_response() -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": "INVALID_REQUEST", "message": "invalid json"},
    }


def run_stdio(tool_executor: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None) -> None:
    """
    Process newline-delimited JSON requests from stdin and write responses to stdout.

    No exceptions are propagated; invalid JSON yields an INVALID_REQUEST error response.
    """
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
                response = handle_request(payload, tool_executor=tool_executor)

            try:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception:  # noqa: BLE001
                # Swallow output errors to honor "no exception" requirement
                return
    except Exception:  # noqa: BLE001
        # Do not propagate exceptions outside run_stdio
        return
