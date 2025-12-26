# MCP Contract v1 (Normative)

## Status
- Version: v1
- Status: Frozen
- Scope: Minimal / Industrial / Auditable

## Standards
- JSON-RPC 2.0
- JSON RFC 8259 / ECMA-404
- UTF-8
- Transport agnostic

## Request Envelope
- JSON object
- `jsonrpc`: string, value MUST be `"2.0"`, required
- `id`: string, required
- `method`: string, required
- `params`: object, required
- Unsupported members are ignored by this contract

## Supported Methods
- Only `tools.call` is accepted
- Any other `method` MUST yield `METHOD_NOT_FOUND`

### tools.call
- `params.tool`: string, required
- `params.arguments`: object, required

## Success Response
- JSON object
- `jsonrpc`: string, value MUST be `"2.0"`
- `id`: mirrors request `id`
- `result.ok`: boolean, MUST be `true`
- `result.data`: object (may be empty)
- MUST NOT contain `error`

## Error Response
- JSON object
- `jsonrpc`: string, value MUST be `"2.0"`
- `id`: mirrors request `id` when available; MAY be `null` when `id` is absent or invalid
- `error.code`: enum value from Error Codes
- `error.message`: string, human-readable, implementation-defined
- MUST NOT include stack traces or debugging details
- MUST NOT contain `result`

## Error Codes (Frozen Enum)
- `INVALID_REQUEST`
- `METHOD_NOT_FOUND`
- `TOOL_NOT_FOUND`
- `INVALID_ARGUMENT`
- `EXECUTION_ERROR`
- `INTERNAL_ERROR`

## Invariants
- `result` XOR `error`; never both and never neither
- Payloads MUST be valid JSON
- UTF-8 encoding for all bytes on the wire
- Schema changes require a new contract version
