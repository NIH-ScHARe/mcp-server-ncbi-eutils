"""Local development entrypoint for the NCBI E-utilities MCP server."""

from eutils_server.app import mcp


if __name__ == "__main__":
    mcp.run(transport="stdio")
