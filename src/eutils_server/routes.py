"""HTTP route registration for the NCBI E-utilities MCP server."""

from fastmcp import FastMCP


def register_routes(mcp: FastMCP) -> None:
    """Register custom HTTP routes."""

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        from starlette.responses import JSONResponse

        return JSONResponse({"status": "ok", "server": "eutils_mcp"})
