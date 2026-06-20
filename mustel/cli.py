# mustel/cli.py
"""
mustel CLI — click-based command line interface.

Commands:
  mustel review                  Full scan, JSON output
  mustel review --file <path>    Single file scan
  mustel review --watch          Re-scan on file change
  mustel env                     Python environment snapshot JSON
  mustel serve                   Start MCP server
"""

from __future__ import annotations

import sys
import json

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
@click.option("--no-packages", is_flag=True, default=False, help="Skip pip-audit (faster).")
@click.option("--audit", "force_audit", is_flag=True, default=None, help="Force Audit Mode (runs Bandit and CVE check).")
@click.option("--pretty", is_flag=True, default=False, help="Pretty-print JSON output.")
def review(path: str, single_file: str, no_packages: bool, force_audit: bool | None, pretty: bool):
    """
    Scan Python and JS/TS code for bugs and security issues.

    Outputs a JSON report conforming to mustel schema v1.
    The 'agent_prompt' field contains a pre-written summary for AI agents.

    Examples:
      mustel review                   # scan current directory
      mustel review ./src             # scan a specific directory
      mustel review --file app.py     # scan one file
      mustel review --no-packages     # skip CVE check (faster)
      mustel review --audit           # force deep security/CVE check
    """
    import os
    # Passive bootstrap check: if .mustel cache folder is missing, run bootstrap silently
    if not os.path.exists(".mustel"):
        try:
            from mustel.bootstrap import bootstrap_global, bootstrap_project
            bootstrap_global()
            bootstrap_project(".")
        except Exception:
            pass

    from mustel.runner import run_review
    report = run_review(
        path=path if not single_file else None,
        single_file=single_file,
        skip_packages=no_packages,
        audit=force_audit,
    )

    indent = 2 if pretty else None
    click.echo(report.to_json(indent=indent if indent else 2))


# ─────────────────────────────────────────────
#  mustel env
# ─────────────────────────────────────────────

def get_env_snapshot() -> dict:
    """Return a complete snapshot of the current Python environment."""
    import platform
    import subprocess
    
    in_venv = sys.prefix != sys.base_prefix
    venv_status = {
        "active": in_venv,
        "path": sys.prefix if in_venv else None,
        "base_python": sys.base_prefix,
    }
    
    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pip", "--version"],
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5,
        )
        parts = out.strip().split()
        pip_status = {
            "version": parts[1] if len(parts) > 1 else "unknown",
            "available": True,
        }
    except Exception:
        pip_status = {"version": None, "available": False}

    return {
        "python_version": sys.version.split()[0],
        "python_path": sys.executable,
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.architecture()[0],
        "venv": venv_status,
        "pip": pip_status,
    }


@main.command("env")
@click.option("--pretty", is_flag=True, default=False, help="Pretty-print JSON output.")
def env_cmd(pretty: bool):
    """
    Show Python environment snapshot as JSON.

    Outputs: Python version, path, venv status, pip version.
    """
    snap = get_env_snapshot()
    click.echo(json.dumps(snap, indent=2 if pretty else None))


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


# ─────────────────────────────────────────────
#  mustel bootstrap
# ─────────────────────────────────────────────

@main.command("bootstrap")
@click.option("--global", "global_install", is_flag=True, default=False, help="Install globally for all IDEs.")
@click.pass_context
def bootstrap_cmd(ctx, global_install):
    """
    Configure Mustel globally for IDEs and locally for the project.
    """
    from mustel.bootstrap import bootstrap_global, bootstrap_project

    if global_install:
        click.echo("Configuring Mustel globally...")
        ide_success = bootstrap_global()
        if ide_success:
            click.echo(f"Successfully registered Mustel globally with: {', '.join(ide_success)}")
        else:
            click.echo("No active global IDE configurations found to update.")
    else:
        click.echo("Configuring Mustel for current project...")
        results = bootstrap_project(".")
        for task, success in results.items():
            status = "Success" if success else "Failed/Skipped"
            click.echo(f"  - {task}: {status}")


if __name__ == "__main__":
    main()
