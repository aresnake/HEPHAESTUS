import json
import os
import sys
import time
from http.client import HTTPConnection
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.fspath(ROOT))

from src.mcp_core.server import handle_request
from src.mcp_core.transport_http import run_http


def start_server(port=0, tool_executor=None):
    server = run_http(port=port, tool_executor=tool_executor)
    assert server is not None
    # Allow the background thread to start
    time.sleep(0.01)
    return server


def stop_server(server):
    server.shutdown()
    server.server_close()


def request_json(server, method="POST", path="/mcp", body=None):
    host, port = server.server_address
    conn = HTTPConnection(host, port, timeout=2)
    headers = {"Content-Type": "application/json"}
    data = json.dumps(body).encode("utf-8") if body is not None else b""
    conn.request(method, path, body=data, headers=headers)
    resp = conn.getresponse()
    payload = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return payload


def test_post_valid_json_returns_valid_response():
    server = start_server()
    try:
        request = {
            "jsonrpc": "2.0",
            "id": "req-1",
            "method": "tools/call",
            "params": {"tool": "echo", "arguments": {}},
        }
        response = request_json(server, body=request)
        assert "error" in response
        assert response["error"]["code"] == "TOOL_NOT_FOUND"
    finally:
        stop_server(server)


def test_post_invalid_json_returns_invalid_request():
    server = start_server()
    try:
        host, port = server.server_address
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("POST", "/mcp", body=b"not-json", headers={"Content-Type": "application/json"})
        resp = conn.getresponse()
        payload = json.loads(resp.read().decode("utf-8"))
        conn.close()
        assert payload["error"]["code"] == "INVALID_REQUEST"
    finally:
        stop_server(server)


def test_post_tools_call_without_executor_returns_tool_not_found():
    server = start_server()
    try:
        request = {
            "jsonrpc": "2.0",
            "id": "req-2",
            "method": "tools/call",
            "params": {"tool": "echo", "arguments": {}},
        }
        response = request_json(server, body=request)
        assert response["error"]["code"] == "TOOL_NOT_FOUND"
        assert response["id"] == "req-2"
    finally:
        stop_server(server)


def test_get_route_returns_method_not_found():
    server = start_server()
    try:
        response = request_json(server, method="GET")
        assert response["error"]["code"] == "METHOD_NOT_FOUND"
    finally:
        stop_server(server)
