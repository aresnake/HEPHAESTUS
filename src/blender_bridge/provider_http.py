"""Blender MCP HTTP provider entrypoint."""

import sys
import time
from pathlib import Path


def main() -> None:
    try:
        src_dir = Path(__file__).resolve().parents[1]
        if src_dir and str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))

        from mcp_core.transport_http import run_http
        from blender_bridge.executor import execute_tool
        from blender_tools import list_tools

        server = run_http(
            host="127.0.0.1",
            port=8765,
            tool_executor=execute_tool,
            tool_lister=list_tools,
        )
        if server is not None:
            try:
                sys.stdout.write("provider_http ready on 127.0.0.1:8765\n")
                sys.stdout.flush()
            except Exception:
                pass
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                break
    except Exception as exc:  # noqa: BLE001
        try:
            sys.stderr.write(f"provider_http error: {exc}\n")
        except Exception:
            pass


if __name__ == "__main__":
    main()
