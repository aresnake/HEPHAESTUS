import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, os.fspath(SRC))

from mcp_daemon.main import execute_tool, handle_stdio_payload


def start_mock_server(response_payload):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", 0))
            _ = self.rfile.read(length)
            data = json.dumps(response_payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format, *args):  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def stop_mock_server(server):
    server.shutdown()
    server.server_close()


def test_execute_tool_success(monkeypatch):
    response_payload = {"jsonrpc": "2.0", "id": "1", "result": {"message": "pong"}}
    server = start_mock_server(response_payload)
    try:
        url = f"http://{server.server_address[0]}:{server.server_address[1]}/mcp"
        monkeypatch.setenv("BLENDER_MCP_HTTP_URL", url)
        result = execute_tool("blender.ping", {})
        assert result == {"message": "pong"}
    finally:
        stop_mock_server(server)


def test_execute_tool_error(monkeypatch):
    response_payload = {"jsonrpc": "2.0", "id": "1", "error": {"code": -32000, "message": "fail"}}
    server = start_mock_server(response_payload)
    try:
        url = f"http://{server.server_address[0]}:{server.server_address[1]}/mcp"
        monkeypatch.setenv("BLENDER_MCP_HTTP_URL", url)
        with pytest.raises(RuntimeError) as excinfo:
            execute_tool("blender.ping", {})
        assert "fail" in str(excinfo.value)
    finally:
        stop_mock_server(server)


def test_initialize_handshake():
    payload = {
        "jsonrpc": "2.0",
        "id": "init-1",
        "method": "initialize",
        "params": {"protocolVersion": "1.2.3"},
    }

    response = handle_stdio_payload(payload, tool_executor=execute_tool)

    assert response["result"]["protocolVersion"] == "1.2.3"
    assert response["result"]["serverInfo"]["name"] == "hephaestus"
