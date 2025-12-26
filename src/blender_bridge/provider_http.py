"""Blender MCP HTTP provider entrypoint."""

import sys
import threading
from pathlib import Path


def main() -> None:
    try:
        src_dir = Path(__file__).resolve().parents[1]
        if src_dir and str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))

        from mcp_core.transport_http import run_http
        from blender_bridge.executor import execute_tool

        thread = threading.Thread(
            target=run_http,
            kwargs={"host": "127.0.0.1", "port": 8765, "tool_executor": execute_tool},
            daemon=True,
        )
        thread.start()
    except Exception as exc:  # noqa: BLE001
        try:
            sys.stderr.write(f"provider_http error: {exc}\n")
        except Exception:
            pass


if __name__ == "__main__":
    main()
