"""Blender MCP provider entrypoint using stdio transport."""

from src.blender_bridge.executor import execute_tool
from src.mcp_core.transport_stdio import run_stdio


def main() -> None:
    try:
        run_stdio(tool_executor=execute_tool)
    except Exception:
        # Silence all exceptions to avoid crashing the host environment.
        return


if __name__ == "__main__":
    main()
