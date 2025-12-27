import os
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.fspath(ROOT))

from src.mcp_core.server import handle_request
from src.blender_tools import list_tools


def test_valid_call_without_tool_executor_returns_tool_not_found():
    request = {
        "jsonrpc": "2.0",
        "id": "req-1",
        "method": "tools/call",
        "params": {"tool": "echo", "arguments": {}},
    }

    response = handle_request(request)

    assert response["error"]["code"] == -32004
    assert response["id"] == "req-1"
    assert "result" not in response


def test_unknown_method_returns_method_not_found():
    request = {
        "jsonrpc": "2.0",
        "id": "req-2",
        "method": "unknown.method",
        "params": {"tool": "echo", "arguments": {}},
    }

    response = handle_request(request)

    assert response["error"]["code"] == -32601
    assert response["id"] == "req-2"


def test_invalid_payload_returns_invalid_request():
    response = handle_request({})

    assert response["error"]["code"] == -32600
    assert response["id"] is None
    assert response["jsonrpc"] == "2.0"


def test_tool_executor_success_returns_result_ok_true():
    def executor(tool_name, arguments):
        assert tool_name == "echo"
        assert arguments == {"value": "hi"}
        return {"echo": arguments["value"]}

    request = {
        "jsonrpc": "2.0",
        "id": "req-3",
        "method": "tools/call",
        "params": {"tool": "echo", "arguments": {"value": "hi"}},
    }

    response = handle_request(request, tool_executor=executor)

    assert "error" not in response
    assert response["result"]["ok"] is True
    assert response["result"]["data"] == {"echo": "hi"}
    assert response["id"] == "req-3"


def test_tool_executor_exception_returns_execution_error():
    def executor(tool_name, arguments):
        raise RuntimeError("boom")

    request = {
        "jsonrpc": "2.0",
        "id": "req-4",
        "method": "tools/call",
        "params": {"tool": "echo", "arguments": {}},
    }

    response = handle_request(request, tool_executor=executor)

    assert response["error"]["code"] == -32003
    assert response["id"] == "req-4"


def test_tools_list_without_lister_returns_empty_list():
    request = {"jsonrpc": "2.0", "id": "req-5", "method": "tools/list", "params": {}}

    response = handle_request(request)

    assert response["result"]["tools"] == []
    assert response["id"] == "req-5"


def test_tools_list_with_lister_returns_tools():
    def tool_lister():
        return [{"name": "echo", "description": "echo back", "input_schema": {"type": "object"}}]

    request = {"jsonrpc": "2.0", "id": "req-6", "method": "tools/list", "params": {}}

    response = handle_request(request, tool_lister=tool_lister)

    assert response["result"]["tools"] == [
        {"name": "echo", "description": "echo back", "input_schema": {"type": "object"}}
    ]
    assert response["id"] == "req-6"


def test_initialize_returns_server_info_and_capabilities():
    request = {
        "jsonrpc": "2.0",
        "id": "init-1",
        "method": "initialize",
        "params": {"protocolVersion": "1.0"},
    }

    response = handle_request(request)

    assert response["result"]["serverInfo"]["name"] == "hephaestus"
    assert response["result"]["serverInfo"]["version"]
    assert response["result"]["capabilities"] == {"tools": {}}
    assert response["result"]["protocolVersion"] == "1.0"


def test_tools_list_includes_blender_tools():
    request = {"jsonrpc": "2.0", "id": "req-7", "method": "tools/list", "params": {}}

    response = handle_request(request, tool_lister=list_tools)

    names = {tool["name"] for tool in response["result"]["tools"]}
    assert "blender.ping" in names
    assert "blender.add_cube" in names
    assert all("input_schema" in tool for tool in response["result"]["tools"])


def test_method_alias_dot_notation():
    request = {
        "jsonrpc": "2.0",
        "id": "req-8",
        "method": "tools.call",
        "params": {"tool": "echo", "arguments": {}},
    }

    response = handle_request(request)

    assert response["error"]["code"] == -32004
    assert response["id"] == "req-8"
    assert response["jsonrpc"] == "2.0"


def test_list_alias_dot_notation():
    request = {"jsonrpc": "2.0", "id": "req-9", "method": "tools.list", "params": {}}

    response = handle_request(request, tool_lister=list_tools)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == "req-9"
    assert isinstance(response["result"]["tools"], list)


def test_initialize_with_numeric_id():
    request = {
        "jsonrpc": "2.0",
        "id": 42,
        "method": "initialize",
        "params": {"protocolVersion": "2.0"},
    }

    response = handle_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 42
    assert response["result"]["protocolVersion"] == "2.0"


def test_tools_list_with_numeric_id():
    request = {"jsonrpc": "2.0", "id": 99, "method": "tools/list", "params": {}}

    response = handle_request(request, tool_lister=list_tools)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 99
    assert isinstance(response["result"]["tools"], list)


def test_invalid_id_object_returns_invalid_request():
    request = {"jsonrpc": "2.0", "id": {"bad": True}, "method": "tools/list", "params": {}}

    response = handle_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] is None
    assert response["error"]["code"] == -32600


def test_invalid_id_array_returns_invalid_request():
    request = {"jsonrpc": "2.0", "id": [1, 2], "method": "tools/list", "params": {}}

    response = handle_request(request)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] is None
    assert response["error"]["code"] == -32600
