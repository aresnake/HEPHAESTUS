"""Blender MCP provider entrypoint executed via blender --python."""

import sys
from pathlib import Path


def main() -> None:
    try:
        src_dir = Path(__file__).resolve().parents[1]
        if src_dir and str(src_dir) not in sys.path:
            sys.path.insert(0, str(src_dir))

        from mcp_core.transport_stdio import run_stdio
        from blender_bridge.executor import execute_tool
        from blender_tools import list_tools

        run_stdio(tool_executor=execute_tool, tool_lister=list_tools)
    except KeyboardInterrupt:
        return
    except Exception as exc:  # noqa: BLE001
        try:
            sys.stderr.write(f"provider error: {exc}\n")
        except Exception:
            pass


if __name__ == "__main__":
    main()
