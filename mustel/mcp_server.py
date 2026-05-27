# mustel/mcp_server.py
"""
mustel MCP server — exposes mustel tools to AI IDEs via the MCP protocol.

Runs on stdio transport (stdin/stdout). No network port needed.
AI IDEs connect by launching: mustel serve

Tools exposed:
  review(path?)          → complete mustel JSON report
  review_file(file_path) → mustel JSON filtered to one file
  env()                  → Python environment snapshot
  check_package(name)    → package availability and vulnerability status

MCP configuration for AI IDEs:
  {
    "mcpServers": {
      "mustel": {
        "command": "mustel",
        "args": ["serve"],
        "description": "Python bug and security detection"
      }
    }
  }
"""

from __future__ import annotations

import json
import sys
import os


def start_mcp_server():
    """
    Start the mustel MCP server on stdio transport.

    This function blocks until the server is stopped.
    """
    try:
        import mcp.server.stdio
        from mcp.server import Server
        from mcp.types import Tool, TextContent
    except ImportError:
        print(
            json.dumps({"error": "mcp package not installed. Run: pip install mcp"}),
            file=sys.stderr,
        )
        sys.exit(1)

    server = Server("mustel")

    # ─────────────────────────────────────────────
    #  Tool: review
    # ─────────────────────────────────────────────

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="review",
                description=(
                    "Scan a Python project for bugs and security issues. "
                    "Returns structured JSON with all findings and an agent_prompt "
                    "field that summarizes what to fix and in what order."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory or file to scan. Defaults to current directory.",
                        },
                        "skip_packages": {
                            "type": "boolean",
                            "description": "Skip pip-audit CVE check for faster scanning.",
                            "default": False,
                        },
                    },
                },
            ),
            Tool(
                name="review_file",
                description=(
                    "Scan a single Python file for bugs and security issues. "
                    "Faster than a full project scan. Use after every file save."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Absolute or relative path to the Python file.",
                        },
                    },
                    "required": ["file_path"],
                },
            ),
            Tool(
                name="env",
                description=(
                    "Get Python environment information: version, path, venv status, pip version. "
                    "Call at session start to configure the interpreter."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            if name == "review":
                from mustel.runner import run_review
                path = arguments.get("path", os.getcwd())
                skip_packages = arguments.get("skip_packages", False)
                report = run_review(path=path, skip_packages=skip_packages)
                return [TextContent(type="text", text=report.to_json(indent=2))]

            elif name == "review_file":
                from mustel.runner import run_review
                file_path = arguments.get("file_path", "")
                if not file_path:
                    return [TextContent(type="text", text=json.dumps({"error": "file_path is required"}))]
                report = run_review(single_file=file_path, skip_packages=True)
                return [TextContent(type="text", text=report.to_json(indent=2))]

            elif name == "env":
                from mustel.env import get_env_snapshot
                snap = get_env_snapshot()
                return [TextContent(type="text", text=json.dumps(snap, indent=2))]

            else:
                return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    # Run the server
    import asyncio

    async def _run():
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(_run())
