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
        from mcp.types import Tool, TextContent, Resource
    except ImportError:
        print(
            json.dumps({"error": "mcp package not installed. Run: pip install mcp"}),
            file=sys.stderr,
        )
        sys.exit(1)

    server = Server("mustel")

    # ─────────────────────────────────────────────
    #  Tools Definition
    # ─────────────────────────────────────────────

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="review",
                description=(
                    "Scan a project (Python, Notebooks, and JS/TS) for bugs and security issues. "
                    "Returns a token-optimized report. Default is compact format."
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
                        "compact": {
                            "type": "boolean",
                            "description": "Output compact, token-saving representation.",
                            "default": True,
                        },
                        "audit": {
                            "type": "boolean",
                            "description": "Force deep Audit Mode (security/CVE check).",
                            "default": False,
                        },
                    },
                },
            ),
            Tool(
                name="review_file",
                description=(
                    "Scan a single file (Python, Notebook, or JS/TS) for bugs. "
                    "Sub-millisecond latency. Use after every file save."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Absolute or relative path to the file.",
                        },
                        "compact": {
                            "type": "boolean",
                            "description": "Output compact, token-saving representation.",
                            "default": True,
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
            Tool(
                name="bootstrap",
                description=(
                    "Auto-configure Mustel globally for IDEs (Cursor/Windsurf/Claude Code) "
                    "and locally for the project (Git hooks and instructions)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "global_install": {
                            "type": "boolean",
                            "description": "Register globally for all IDEs.",
                            "default": False,
                        },
                    },
                },
            ),
            Tool(
                name="get_code_map",
                description=(
                    "Generate a compact, token-dense skeleton (class names, function signatures) "
                    "of your project files. Use at session start to understand codebase layout."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory to scan. Defaults to current directory.",
                        },
                    },
                },
            ),
        ]

    # ─────────────────────────────────────────────
    #  Tools Execution
    # ─────────────────────────────────────────────

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            if name == "review":
                from mustel.runner import run_review
                path = arguments.get("path", os.getcwd())
                skip_packages = arguments.get("skip_packages", False)
                compact = arguments.get("compact", True)
                audit = arguments.get("audit", False)
                report = run_review(path=path, skip_packages=skip_packages, audit=audit)
                return [TextContent(type="text", text=report.to_json(indent=2, compact=compact))]

            elif name == "review_file":
                from mustel.runner import run_review
                file_path = arguments.get("file_path", "")
                compact = arguments.get("compact", True)
                if not file_path:
                    return [TextContent(type="text", text=json.dumps({"error": "file_path is required"}))]
                # Always run in Dev Mode for review_file
                report = run_review(single_file=file_path, skip_packages=True, audit=False)
                output_text = report.to_json(indent=2, compact=compact)
                if report.summary.total_errors > 0:
                    output_text += (
                        "\n\n=== MUSTEL GUARDRAIL ALERT ===\n"
                        "Syntax/import errors detected! You must fix these errors immediately "
                        "before showing changes to the user or running the code."
                    )
                return [TextContent(type="text", text=output_text)]

            elif name == "env":
                from mustel.cli import get_env_snapshot
                snap = get_env_snapshot()
                return [TextContent(type="text", text=json.dumps(snap, indent=2))]

            elif name == "bootstrap":
                from mustel.bootstrap import bootstrap_global, bootstrap_project
                global_install = arguments.get("global_install", False)
                if global_install:
                    ide_success = bootstrap_global()
                    msg = f"Successfully registered Mustel globally with: {', '.join(ide_success)}" if ide_success else "No active global IDE configurations found to update."
                else:
                    results = bootstrap_project(".")
                    msg = "Project bootstrapped: " + ", ".join([f"{k}: {'success' if v else 'failed'}" for k, v in results.items()])
                return [TextContent(type="text", text=msg)]

            elif name == "get_code_map":
                from mustel.code_map import format_code_map_text
                path = arguments.get("path", os.getcwd())
                return [TextContent(type="text", text=format_code_map_text(path))]

            else:
                return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    # ─────────────────────────────────────────────
    #  Resources Definition
    # ─────────────────────────────────────────────

    @server.list_resources()
    async def list_resources():
        return [
            Resource(
                uri="mustel://report",
                name="Mustel Project Review Report",
                description="The latest Mustel static analysis report for the project (Dev Mode, compact format).",
                mimeType="application/json",
            )
		]

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        if uri == "mustel://report":
            from mustel.runner import run_review
            report = run_review(path=os.getcwd(), skip_packages=True, audit=False)
            return report.to_json(indent=2, compact=True)
        raise ValueError(f"Unknown resource URI: {uri}")

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
