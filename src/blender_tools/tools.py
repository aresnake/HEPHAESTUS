"""Static tool definitions for the Blender MCP provider."""

TOOLS = [
    {
        "name": "blender.ping",
        "description": "Respond with a pong message to verify connectivity.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "blender.add_cube",
        "description": "Add a cube to the current Blender scene.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def list_tools() -> list:
    """Return supported tool descriptors."""
    return TOOLS
