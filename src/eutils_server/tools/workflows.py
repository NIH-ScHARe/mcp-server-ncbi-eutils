"""Workflow-oriented tool registrations built on top of the core utilities."""

from fastmcp import FastMCP


def register_workflow_tools(mcp: FastMCP) -> None:
    """Register higher-level workflow helpers.

    Tool names reserved for implementation:
    - eutils_search_and_summary
    - eutils_search_and_fetch
    - eutils_find_related
    """

    return None
