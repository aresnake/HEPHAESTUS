import pytest


ERROR_CODES = {
    -32700,
    -32600,
    -32601,
    -32602,
    -32603,
    -32004,
    -32003,
}


def validate_request(payload: dict) -> bool:
    """Validate request envelope shape against MCP Contract v1."""
    if not isinstance(payload, dict):
        return False
    required_keys = {"jsonrpc", "method", "params"}
    if payload.get("jsonrpc") != "2.0":
        return False
    if not required_keys.issubset(payload):
        return False
    if "id" in payload and not (
        isinstance(payload["id"], (str, int, float)) or payload["id"] is None
    ):
        return False
    if not isinstance(payload["method"], str):
        return False
    if payload["method"] not in {"tools/call", "tools.call"}:
        return False
    if not isinstance(payload["params"], dict):
        return False
    if not isinstance(payload["params"].get("tool"), str):
        return False
    if not isinstance(payload["params"].get("arguments"), dict):
        return False
    return True


def validate_response(payload: dict) -> bool:
    """Validate response envelope shape and invariants."""
    if not isinstance(payload, dict):
        return False
    if payload.get("jsonrpc") != "2.0":
        return False

    has_result = "result" in payload
    has_error = "error" in payload
    if has_result == has_error:
        return False

    if "id" not in payload:
        return False

    if has_result:
        result = payload["result"]
        if not isinstance(result, dict):
            return False
        if result.get("ok") is not True:
            return False
        if not isinstance(result.get("data"), dict):
            return False

    if has_error:
        error = payload["error"]
        if not isinstance(error, dict):
            return False
        if not isinstance(error.get("code"), int):
            return False
        if error["code"] not in ERROR_CODES:
            return False
        if not isinstance(error.get("message"), str):
            return False
        if "stack" in error or "trace" in error:
            return False

    return True


def test_minimal_valid_request():
    payload = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/call",
        "params": {
            "tool": "echo",
            "arguments": {},
        },
    }
    assert validate_request(payload)


def test_request_allows_numeric_id():
    payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"tool": "echo", "arguments": {}},
    }
    assert validate_request(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "jsonrpc": "2.0",
            "id": "1",
            "params": {"tool": "echo", "arguments": {}},
        },
        {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "tools/call",
        },
    ],
    ids=["missing-method", "missing-params"],
)
def test_request_missing_required_field(payload):
    assert not validate_request(payload)


@pytest.mark.parametrize(
    "invalid_id",
    [{}, [], ["a"]],
)
def test_request_invalid_id_types(invalid_id):
    payload = {
        "jsonrpc": "2.0",
        "id": invalid_id,
        "method": "tools/call",
        "params": {"tool": "echo", "arguments": {}},
    }
    assert not validate_request(payload)


def test_response_result_and_error_are_exclusive():
    base = {"jsonrpc": "2.0", "id": "1"}
    invalid = {
        **base,
        "result": {"ok": True, "data": {}},
        "error": {"code": -32603, "message": "unexpected"},
    }
    success = {**base, "result": {"ok": True, "data": {}}}
    failure = {
        **base,
        "error": {"code": -32004, "message": "missing tool"},
    }

    assert not validate_response(invalid)
    assert validate_response(success)
    assert validate_response(failure)
