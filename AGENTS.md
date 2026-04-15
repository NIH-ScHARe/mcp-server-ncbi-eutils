Use the repo-local skill at `.codex/skills/mcp-builder/SKILL.md` when working on MCP server architecture, tool design, transport decisions, API integration patterns, implementation structure, testing, or evaluation creation in this repository.

Load additional guidance from `.codex/skills/mcp-builder/references/` only as needed:
- `mcp_best_practices.md` for general MCP design and response conventions
- `python_mcp_server.md` for Python/FastMCP implementation patterns
- `node_mcp_server.md` only if the repo shifts to Node/TypeScript
- `evaluation.md` when creating evals or benchmark questions

Prefer Python for this repository unless the user explicitly asks for a different stack.

Keep MCP server entrypoint code minimal. Put transport and server initialization in the app entrypoint, tool registration in a dedicated tools module, and shared models/helpers in separate modules as the codebase grows.

Prefer comprehensive, clearly named tools over overly narrow workflow wrappers unless the user asks for a specialized workflow.

Design tool inputs, outputs, descriptions, and error messages for agent usability:
- use explicit parameter names and validation
- support filtering and pagination where appropriate
- return concise, structured, easy-to-scan results
- make error messages actionable

When implementing or changing tools, verify the behavior locally when possible and keep read-only exploration separate from write operations.
