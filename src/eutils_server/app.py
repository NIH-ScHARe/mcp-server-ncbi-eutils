import os

from fastmcp import FastMCP

from eutils_server.routes import register_routes
from eutils_server.tools import register_tools

mcp = FastMCP("eutils_mcp")

register_routes(mcp)
register_tools(mcp)

app = mcp.http_app(stateless_http=True)

if __name__ == "__main__":
    port_env = os.environ.get("DATABRICKS_APP_PORT") or os.environ.get("PORT")
    if port_env:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=int(port_env))
    else:
        mcp.run(transport="stdio")
