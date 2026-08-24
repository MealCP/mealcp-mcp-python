"""Entry point: ``mealcp-mcp`` or ``python -m mealcp_mcp``.

Runs the MCP server on stdio (the transport used by Claude for Desktop and
other MCP hosts). Never write to stdout here — it corrupts the JSON-RPC
protocol.
"""

from __future__ import annotations

from mealcp_mcp.server import mcp


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
