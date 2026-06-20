# mustel/bootstrap.py
"""
mustel bootstrap — global and local configuration injector.
Automatically configures Cursor, Windsurf, Claude Code, Git hooks, and rules.
"""

from __future__ import annotations

import os
import sys
import json
import stat
from typing import Dict, Any, List

# The MCP server entry to be injected
MUSTEL_MCP_SERVER = {
    "command": "mustel",
    "args": ["serve"],
    "description": "Mustel — Agent-Native Linter & Guardrail",
}


def expand_path(path: str) -> str:
    """Expand environment variables and user home shortcuts in a path."""
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def get_global_configs() -> Dict[str, str]:
    """Get the mapping of IDE names to their global MCP config file paths."""
    home = os.path.expanduser("~")
    
    # OS-specific locations
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
        claude_desktop = os.path.join(appdata, "Claude", "claude_desktop_config.json")
        cursor = os.path.join(home, ".cursor", "mcp.json")
    elif sys.platform == "darwin":
        claude_desktop = os.path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json")
        cursor = os.path.join(home, ".cursor", "mcp.json")
    else:
        # Linux / Fallback
        claude_desktop = os.path.join(home, ".config", "Claude", "claude_desktop_config.json")
        cursor = os.path.join(home, ".cursor", "mcp.json")

    return {
        "Cursor": cursor,
        "Windsurf": os.path.join(home, ".codeium", "windsurf", "mcp_config.json"),
        "Claude Code": os.path.join(home, ".claude.json"),
        "Claude Desktop": claude_desktop,
    }


def inject_into_json_file(file_path: str, mcp_key: str = "mcpServers") -> bool:
    """
    Safely inject the Mustel MCP server definition into a JSON config file.
    Creates the directory and file if they do not exist.
    """
    abs_path = expand_path(file_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)
    
    data: Dict[str, Any] = {}
    if os.path.exists(abs_path):
        try:
            # Create a backup first
            backup_path = abs_path + ".bak"
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            data = json.loads(content)
            if not isinstance(data, dict):
                return False
        except Exception:
            return False

    # Ensure mcp_key exists and is a dictionary
    if mcp_key not in data or not isinstance(data[mcp_key], dict):
        data[mcp_key] = {}

    # Inject or update
    data[mcp_key]["mustel"] = MUSTEL_MCP_SERVER

    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def bootstrap_global() -> List[str]:
    """
    Register Mustel globally across all active IDEs.
    Returns a list of successfully configured IDEs.
    """
    successes = []
    configs = get_global_configs()
    
    for ide, path in configs.items():
        # For Claude Desktop / Windsurf / Claude Code / Cursor, we update the mcpServers key
        # Claude Desktop and Claude Code config keys are slightly different or standard
        # Cursor: mcpServers, Windsurf: mcpServers, Claude Desktop: mcpServers, Claude Code: mcpServers
        key = "mcpServers"
        
        # Inject config
        if inject_into_json_file(path, mcp_key=key):
            successes.append(ide)
            
    return successes


def bootstrap_project(project_path: str) -> Dict[str, bool]:
    """
    Bootstrap the project directory with:
    1. Project-scoped Cursor / Claude Code MCP configs (.cursor/mcp.json, .mcp.json)
    2. .cursorrules / .windsurfrules append
    3. Git pre-commit hook
    """
    root = os.path.abspath(project_path)
    results = {}

    # 1. Project-scoped MCP JSON files
    cursor_proj = os.path.join(root, ".cursor", "mcp.json")
    claude_proj = os.path.join(root, ".mcp.json")
    
    results["cursor_config"] = inject_into_json_file(cursor_proj)
    results["claude_config"] = inject_into_json_file(claude_proj)

    # 2. Rules injection (.cursorrules / .windsurfrules)
    rule_files = [".cursorrules", ".windsurfrules"]
    rules_text = (
        "\n\n# --- MUSTEL AGENT GUARDRAILS ---\n"
        "# Before proposing or finalizing code changes, you must run the mustel review tool.\n"
        "# Call the `review` or `review_file` MCP tool to verify syntax, bugs, and standards.\n"
        "# Fix all reported errors and security vulnerabilities before showing changes to the user.\n"
        "# --- END MUSTEL AGENT GUARDRAILS ---\n"
    )
    
    for rule_file in rule_files:
        rule_path = os.path.join(root, rule_file)
        try:
            exists = os.path.exists(rule_path)
            mode = "a" if exists else "w"
            
            # If exists, check if already injected
            if exists:
                with open(rule_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "MUSTEL AGENT GUARDRAILS" in content:
                    results[rule_file] = True
                    continue
                    
            with open(rule_path, mode, encoding="utf-8") as f:
                f.write(rules_text)
            results[rule_file] = True
        except Exception:
            results[rule_file] = False

    # 3. Git pre-commit hook
    git_dir = os.path.join(root, ".git")
    if os.path.isdir(git_dir):
        hooks_dir = os.path.join(git_dir, "hooks")
        os.makedirs(hooks_dir, exist_ok=True)
        hook_path = os.path.join(hooks_dir, "pre-commit")
        
        # Git pre-commit shell script
        hook_content = (
            "#!/bin/sh\n"
            "# mustel git pre-commit hook\n"
            "echo \"[mustel] Running pre-commit static analysis guardrail...\"\n"
            "mustel review\n"
            "if [ $? -ne 0 ]; then\n"
            "  echo \"[mustel] Scan failed! Please resolve issues before committing.\"\n"
            "  exit 1\n"
            "fi\n"
        )
        
        try:
            # We don't overwrite if existing hook is custom, but we can write if clean
            write_hook = True
            if os.path.exists(hook_path):
                with open(hook_path, "r", encoding="utf-8") as f:
                    existing = f.read()
                if "mustel review" in existing:
                    write_hook = False
                else:
                    # Prepend it after shebang if present, otherwise prepend
                    mustel_hook_text = "# mustel hook\nmustel review || exit 1\n"
                    lines = existing.splitlines(keepends=True)
                    if lines and lines[0].startswith("#!"):
                        shebang = lines[0]
                        rest = "".join(lines[1:])
                        hook_content = shebang + "\n" + mustel_hook_text + "\n" + rest
                    else:
                        hook_content = mustel_hook_text + "\n" + existing
            
            if write_hook:
                with open(hook_path, "w", encoding="utf-8", newline="\n") as f:
                    f.write(hook_content)
                
                # Make hook executable on POSIX systems
                if sys.platform != "win32":
                    st = os.stat(hook_path)
                    os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
                    
            results["git_hook"] = True
        except Exception:
            results["git_hook"] = False
    else:
        results["git_hook"] = False

    return results
