"""Tool executor mapping Blender tools to MCP calls."""

import bpy


def execute_tool(tool_name: str, arguments: dict) -> dict:
    """
    Execute a Blender tool by name.

    Raises:
        KeyError: when tool_name is not supported.
    """
    if tool_name == "blender.ping":
        return {"message": "pong"}
    if tool_name == "blender.add_cube":
        bpy.ops.mesh.primitive_cube_add()
        return {"object": "Cube"}
    raise KeyError(tool_name)
