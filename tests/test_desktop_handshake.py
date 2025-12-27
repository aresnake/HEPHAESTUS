import json
import os
import sys
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.fspath(ROOT))

from src.mcp_core.transport_stdio import run_stdio
from src.blender_tools import list_tools


def run_sequence(lines: str):
    stdin = StringIO(lines)
    stdout = StringIO()
    orig_stdin, orig_stdout = sys.stdin, sys.stdout
    sys.stdin, sys.stdout = stdin, stdout

    def executor(tool_name, arguments):
        if tool_name == "blender.ping":
            return {"message": "pong"}
        raise KeyError(tool_name)

    try:
        run_stdio(tool_executor=executor, tool_lister=list_tools)
    finally:
        sys.stdin, sys.stdout = orig_stdin, orig_stdout
    return stdout.getvalue().splitlines()


def test_desktop_handshake_sequence():
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "1.0"},
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "blender.ping", "arguments": {}},
        },
    ]
    input_data = "\n".join(json.dumps(m) for m in messages) + "\n"

    lines = run_sequence(input_data)

    assert len(lines) == 3

    init_resp = json.loads(lines[0])
    list_resp = json.loads(lines[1])
    call_resp = json.loads(lines[2])

    assert init_resp["jsonrpc"] == "2.0"
    assert init_resp["id"] == 1
    assert "result" in init_resp

    assert list_resp["jsonrpc"] == "2.0"
    assert list_resp["id"] == 2
    assert isinstance(list_resp["result"]["tools"], list)

    assert call_resp["jsonrpc"] == "2.0"
    assert call_resp["id"] == 3
    assert call_resp["result"]["data"]["message"] == "pong"
