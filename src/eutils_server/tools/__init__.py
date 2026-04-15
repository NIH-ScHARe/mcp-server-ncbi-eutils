"""Tool registration package for the NCBI E-utilities server."""

from fastmcp import FastMCP

from .core import register_core_tools
from .workflows import register_workflow_tools


def register_tools(mcp: FastMCP) -> None:
    """Register all NCBI E-utilities tools with the MCP server."""
    register_core_tools(mcp)
    register_workflow_tools(mcp)
