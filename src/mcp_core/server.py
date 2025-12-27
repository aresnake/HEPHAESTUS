"""Minimal MCP Core handler for MCP Contract v1."""

from typing import Any, Callable, Dict, Optional


ErrorResponse = Dict[str, Any]
SuccessResponse = Dict[str, Any]
ToolExecutor = Optional[Callable[[str, Dict[str, Any]], Dict[str, Any]]]
ToolLister = Optional[Callable[[], list]]

SERVER_INFO = {"name": "hephaestus", "version": "0.1.0"}

ERROR_CODES = {
    "INVALID_REQUEST",
    "METHOD_NOT_FOUND",
    "TOOL_NOT_FOUND",
    "INVALID_ARGUMENT",
    "EXECUTION_ERROR",
    "INTERNAL_ERROR",
}


def _error_response(code: str, message: str, request_id: Optional[str]) -> ErrorResponse:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _success_response(request_id: str, data: Dict[str, Any]) -> SuccessResponse:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"ok": True, "data": data},
    }


def _list_tools_response(request_id: str, tools: list) -> SuccessResponse:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": tools},
    }


def _initialize_response(request_id: str, protocol_version: str) -> SuccessResponse:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": protocol_version,
            "capabilities": {"tools": {}},
            "serverInfo": SERVER_INFO,
        },
    }


def handle_request(
    payload: dict,
    tool_executor: ToolExecutor = None,
    tool_lister: ToolLister = None,
) -> dict:
    """
    Handle a single MCP request payload according to MCP Contract v1.

    All validation and execution errors are converted to MCP error responses.
    """
    request_id: Optional[str] = None
    try:
        if not isinstance(payload, dict):
            return _error_response("INVALID_REQUEST", "payload must be object", None)

        if payload.get("jsonrpc") != "2.0":
            return _error_response("INVALID_REQUEST", "jsonrpc must be '2.0'", None)

        if "id" not in payload or "method" not in payload or "params" not in payload:
            return _error_response("INVALID_REQUEST", "missing required fields", payload.get("id"))

        request_id = payload["id"]
        method = payload["method"]
        params = payload["params"]

        if not isinstance(request_id, str):
            return _error_response("INVALID_REQUEST", "id must be string", None)
        if not isinstance(method, str):
            return _error_response("INVALID_REQUEST", "method must be string", request_id)
        if not isinstance(params, dict):
            return _error_response("INVALID_REQUEST", "params must be object", request_id)

        if method in {"initialize"}:
            if not isinstance(params, dict):
                return _error_response("INVALID_REQUEST", "params must be object", request_id)
            protocol_version = params.get("protocolVersion")
            if not isinstance(protocol_version, str):
                protocol_version = ""
            return _initialize_response(request_id, protocol_version)

        if method in {"tools.list", "tools/list"}:
            if not isinstance(params, dict):
                return _error_response("INVALID_REQUEST", "params must be object", request_id)
            try:
                tools = [] if tool_lister is None else tool_lister()
            except Exception as exc:  # noqa: BLE001
                return _error_response("EXECUTION_ERROR", str(exc) or "execution error", request_id)

            if not isinstance(tools, list):
                return _error_response("EXECUTION_ERROR", "tool lister returned non-list", request_id)

            return _list_tools_response(request_id, tools)

        if method not in {"tools.call", "tools/call"}:
            return _error_response("METHOD_NOT_FOUND", "unsupported method", request_id)

        tool_name = params.get("tool")
        arguments = params.get("arguments")

        if not isinstance(tool_name, str):
            return _error_response("INVALID_REQUEST", "params.tool must be string", request_id)
        if not isinstance(arguments, dict):
            return _error_response("INVALID_REQUEST", "params.arguments must be object", request_id)

        if tool_executor is None:
            return _error_response("TOOL_NOT_FOUND", "no tool executor available", request_id)

        try:
            result_data = tool_executor(tool_name, arguments)
        except Exception as exc:  # noqa: BLE001
            return _error_response("EXECUTION_ERROR", str(exc) or "execution error", request_id)

        if not isinstance(result_data, dict):
            return _error_response("EXECUTION_ERROR", "tool returned non-object", request_id)

        return _success_response(request_id, result_data)

    except Exception as exc:  # noqa: BLE001
        return _error_response("INTERNAL_ERROR", str(exc) or "internal error", request_id)
