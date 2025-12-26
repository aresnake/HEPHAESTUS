"""Minimal HTTP transport for MCP Core."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable, Dict, Optional

from .server import handle_request


def _invalid_json_response() -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": "INVALID_REQUEST", "message": "invalid json"},
    }


def _method_not_found_response() -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": None,
        "error": {"code": "METHOD_NOT_FOUND", "message": "unsupported route or method"},
    }


def _build_handler(tool_executor: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]]):
    class MCPRequestHandler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            try:
                if self.path != "/mcp":
                    response = _method_not_found_response()
                else:
                    length = int(self.headers.get("Content-Length", 0))
                    raw_body = self.rfile.read(length) if length > 0 else b""
                    try:
                        payload = json.loads(raw_body.decode("utf-8"))
                    except Exception:  # noqa: BLE001
                        response = _invalid_json_response()
                    else:
                        response = handle_request(payload, tool_executor=tool_executor)
                self._write_json(response)
            except Exception:  # noqa: BLE001
                self._write_json(_invalid_json_response())

        def do_GET(self) -> None:  # noqa: N802
            self._write_json(_method_not_found_response())

        def do_PUT(self) -> None:  # noqa: N802
            self._write_json(_method_not_found_response())

        def do_DELETE(self) -> None:  # noqa: N802
            self._write_json(_method_not_found_response())

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _write_json(self, body: Dict[str, Any]) -> None:
            try:
                data = json.dumps(body).encode("utf-8")
            except Exception:  # noqa: BLE001
                data = json.dumps(_invalid_json_response()).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except Exception:  # noqa: BLE001
                return

    return MCPRequestHandler


def run_http(
    host: str = "127.0.0.1",
    port: int = 8765,
    tool_executor: Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]] = None,
):
    """
    Start an HTTP server that processes MCP requests on POST /mcp.

    Returns the server instance so callers can manage its lifecycle.
    """
    try:
        handler = _build_handler(tool_executor)
        httpd = HTTPServer((host, port), handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return httpd
    except Exception:  # noqa: BLE001
        return None
