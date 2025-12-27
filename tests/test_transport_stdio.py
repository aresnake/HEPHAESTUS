import json
import os
import sys
from io import StringIO
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.fspath(ROOT))

from src.mcp_core.server import handle_request
from src.mcp_core.transport_stdio import run_stdio


def run_with_io(input_lines):
    stdin = StringIO(input_lines)
    stdout = StringIO()
    orig_stdin, orig_stdout = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = stdin, stdout
    try:
        run_stdio()
    finally:
        sys.stdin, sys.stdout = orig_stdin, orig_stdout
    return stdout.getvalue().splitlines()


def test_valid_json_line_produces_valid_json_response():
    request = {
        "jsonrpc": "2.0",
        "id": "req-1",
        "method": "tools/call",
        "params": {"tool": "echo", "arguments": {}},
    }
    output_lines = run_with_io(json.dumps(request) + "\n")

    assert len(output_lines) == 1
    response = json.loads(output_lines[0])
    assert response["jsonrpc"] == "2.0"
    assert "error" in response
    assert response["error"]["code"] == -32004


def test_invalid_json_line_returns_invalid_request_error():
    output_lines = run_with_io("not-json\n")

    assert len(output_lines) == 1
    response = json.loads(output_lines[0])
    assert response["jsonrpc"] == "2.0"
    assert response["error"]["code"] == -32700
    assert response["id"] is None


def test_tools_call_without_executor_returns_tool_not_found():
    request = {
        "jsonrpc": "2.0",
        "id": "req-2",
        "method": "tools/call",
        "params": {"tool": "echo", "arguments": {}},
    }
    output_lines = run_with_io(json.dumps(request) + "\n")

    response = json.loads(output_lines[0])
    assert response["jsonrpc"] == "2.0"
    assert response["error"]["code"] == -32004
    assert response["id"] == "req-2"


def test_stdout_contains_only_responses():
    request = {
        "jsonrpc": "2.0",
        "id": "req-3",
        "method": "tools/call",
        "params": {"tool": "echo", "arguments": {}},
    }
    lines = run_with_io(json.dumps(request) + "\n")
    assert len(lines) == 1
    assert lines[0].strip().startswith("{") and lines[0].strip().endswith("}")


def test_valid_json_invalid_request_returns_invalid_request_code():
    output_lines = run_with_io('{"jsonrpc":"2.0"}\n')

    response = json.loads(output_lines[0])
    assert response["jsonrpc"] == "2.0"
    assert response["error"]["code"] == -32600
    assert response["id"] is None
