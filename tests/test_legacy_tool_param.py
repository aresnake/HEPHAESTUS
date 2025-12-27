import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.fspath(ROOT))

from src.mcp_core.server import handle_request


def test_legacy_tool_param_still_works():
    request = {
        "jsonrpc": "2.0",
        "id": "legacy-1",
        "method": "tools/call",
        "params": {"tool": "echo", "arguments": {}},
    }

    def executor(tool_name, arguments):
        assert tool_name == "echo"
        return {"echo": "ok"}

    response = handle_request(request, tool_executor=executor)

    assert response["jsonrpc"] == "2.0"
    assert response["id"] == "legacy-1"
    assert response["result"]["data"]["echo"] == "ok"
