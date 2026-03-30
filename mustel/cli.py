# mustel/cli.py
"""
mustel CLI — click-based command line interface.

Commands:
  mustel review                  Full scan, JSON output
  mustel review --file <path>    Single file scan
  mustel review --watch          Re-scan on file change
  mustel env                     Python environment snapshot JSON
  mustel check <pkg>             Package availability check JSON
  mustel install <pkg>           Safe package install
  mustel venv                    Venv status JSON
  mustel venv new                Create .venv in current directory
  mustel serve                   Start MCP server
"""

from __future__ import annotations

import sys
import json
import os
import platform

import click

import mustel as mustel_pkg


@click.group(invoke_without_command=True)
@click.version_option(version=mustel_pkg.__version__, prog_name="mustel")
@click.pass_context
def main(ctx: click.Context):
    """
    mustel — non-AI bug and security detection for AI IDEs.

    Run 'mustel review' to scan your project.
    Run 'mustel serve' to start the MCP server.
    """
    if ctx.invoked_subcommand is None:
        # Default: show help
        click.echo(ctx.get_help())


# ─────────────────────────────────────────────
#  mustel review
# ─────────────────────────────────────────────

@main.command("review")
@click.argument("path", default=".", required=False)
@click.option("--file", "single_file", default=None, help="Scan a single file only.")
@click.option("--watch", is_flag=True, default=False, help="Re-scan on file change.")
@click.option("--no-packages", is_flag=True, default=False, help="Skip pip-audit (faster).")
@click.option("--pretty", is_flag=True, default=False, help="Pretty-print JSON output.")
def review(path: str, single_file: str, watch: bool, no_packages: bool, pretty: bool):
    """
    Scan Python code for bugs and security issues.

    Outputs a JSON report conforming to mustel schema v1.
    The 'agent_prompt' field contains a pre-written summary for AI agents.

    Examples:
      mustel review                   # scan current directory
      mustel review ./src             # scan a specific directory
      mustel review --file app.py     # scan one file
      mustel review --watch           # auto-scan on save
      mustel review --no-packages     # skip CVE check (faster)
    """
    if watch:
        _run_watch(path, no_packages=no_packages)
        return

    from mustel.runner import run_review
    report = run_review(
        path=path if not single_file else None,
        single_file=single_file,
        skip_packages=no_packages,
    )

    indent = 2 if pretty else None
    click.echo(report.to_json(indent=indent if indent else 2))


def _run_watch(path: str, no_packages: bool = False):
    """Run review in watch mode."""
    try:
        from mustel.watcher import start_watch
        start_watch(path, no_packages=no_packages)
    except ImportError:
        click.echo(
            json.dumps({"error": "watchdog not installed. Run: pip install watchdog"}),
            err=True,
        )
        sys.exit(1)


# ─────────────────────────────────────────────
#  mustel env
# ─────────────────────────────────────────────

@main.command("env")
@click.option("--pretty", is_flag=True, default=False, help="Pretty-print JSON output.")
def env_cmd(pretty: bool):
    """
    Show Python environment snapshot as JSON.

    Outputs: Python version, path, venv status, pip version.
    """
    from mustel.env import get_env_snapshot
    snap = get_env_snapshot()
    click.echo(json.dumps(snap, indent=2 if pretty else None))


# ─────────────────────────────────────────────
#  mustel check
# ─────────────────────────────────────────────

@main.command("check")
@click.argument("package")
@click.option("--pretty", is_flag=True, default=False, help="Pretty-print JSON output.")
def check_cmd(package: str, pretty: bool):
    """
    Check if a Python package is installed.

    Outputs: {available, version, importable}
    """
    from mustel.env import check_package
    result = check_package(package)
    click.echo(json.dumps(result, indent=2 if pretty else None))


# ─────────────────────────────────────────────
#  mustel install
# ─────────────────────────────────────────────

@main.command("install")
@click.argument("package")
def install_cmd(package: str):
    """
    Install a Python package using the current Python's pip.

    Outputs: {success, message, package}
    """
    from mustel.env import install_package
    result = install_package(package)
    click.echo(json.dumps(result, indent=2))
    if not result["success"]:
        sys.exit(1)


# ─────────────────────────────────────────────
#  mustel venv
# ─────────────────────────────────────────────

@main.group("venv", invoke_without_command=True)
@click.pass_context
def venv_group(ctx: click.Context):
    """Virtual environment management."""
    if ctx.invoked_subcommand is None:
        _venv_status()


def _venv_status():
    """Show venv status for current directory."""
    from mustel.env import get_venv_status
    status = get_venv_status(".")
    click.echo(json.dumps(status, indent=2))


@venv_group.command("new")
@click.argument("name", default=".venv", required=False)
def venv_new(name: str):
    """
    Create a new virtual environment in the current directory.

    NAME defaults to .venv.
    """
    from mustel.env import create_venv
    result = create_venv(name)
    click.echo(json.dumps(result, indent=2))
    if not result["success"]:
        sys.exit(1)


# ─────────────────────────────────────────────
#  mustel serve (MCP server)
# ─────────────────────────────────────────────

@main.command("serve")
def serve_cmd():
    """
    Start the mustel MCP server.

    Runs on stdio transport (stdin/stdout) — no network port.
    AI IDEs connect via their MCP configuration.

    To configure in an AI IDE, add to MCP config:
      {
        "mcpServers": {
          "mustel": {
            "command": "mustel",
            "args": ["serve"]
          }
        }
      }
    """
    try:
        from mustel.mcp_server import start_mcp_server
        start_mcp_server()
    except ImportError as e:
        click.echo(
            json.dumps({"error": f"MCP dependencies missing: {e}. Run: pip install mcp"}),
            err=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
