# mustel/code_map.py
"""
mustel code_map — AST and regex-based repository skeleton mapper.
Generates highly compact codebase skeletons for AI agents.
"""

from __future__ import annotations

import os
import ast
import re
from typing import Dict, Any, List, Optional
from mustel.runner import _find_all_files


def _parse_python_source(source: str, file_path: str) -> dict:
    """Parse Python source code using AST and extract class/function structures."""
    try:
        tree = ast.parse(source, filename=file_path)
    except Exception as e:
        return {"error": f"SyntaxError: {e}"}

    classes = []
    functions = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_info = {
                "name": node.name,
                "methods": [],
                "docstring": (ast.get_docstring(node) or "").splitlines()[0] if ast.get_docstring(node) else ""
            }
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Extract argument names
                    args = [arg.arg for arg in item.args.args if arg.arg != "self"]
                    doc = (ast.get_docstring(item) or "").splitlines()[0] if ast.get_docstring(item) else ""
                    class_info["methods"].append({
                        "name": item.name,
                        "args": args,
                        "docstring": doc[:60] + "..." if len(doc) > 60 else doc
                    })
            classes.append(class_info)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = [arg.arg for arg in node.args.args]
            doc = (ast.get_docstring(node) or "").splitlines()[0] if ast.get_docstring(node) else ""
            functions.append({
                "name": node.name,
                "args": args,
                "docstring": doc[:60] + "..." if len(doc) > 60 else doc
            })

    return {"classes": classes, "functions": functions}


def _parse_ipynb_file(file_path: str) -> dict:
    """Extract and parse code cells from Jupyter Notebook."""
    import json
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        code_cells = []
        for cell in data.get("cells", []):
            if cell.get("cell_type") == "code":
                cell_source = cell.get("source", [])
                if isinstance(cell_source, list):
                    code_cells.append("".join(cell_source))
                elif isinstance(cell_source, str):
                    code_cells.append(cell_source)
        virtual_py = "\n\n".join(code_cells)
        return _parse_python_source(virtual_py, file_path)
    except Exception as e:
        return {"error": str(e)}


def _parse_js_ts_file(file_path: str) -> dict:
    """Extract JS/TS skeleton using regex parsing."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        return {"error": str(e)}

    class_pattern = re.compile(r"\bclass\s+([A-Za-z0-9_$]+)")
    func_pattern = re.compile(r"\bfunction\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)")
    arrow_pattern = re.compile(r"\b(?:const|let|var)\s+([A-Za-z0-9_$]+)\s*=\s*(?:\([^)]*\)|[A-Za-z0-9_$]+)\s*=>")

    classes = []
    functions = []

    # Very basic scanner
    lines = content.splitlines()
    current_class = None

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("//") or line_stripped.startswith("*"):
            continue

        class_match = class_pattern.search(line_stripped)
        if class_match:
            current_class = {
                "name": class_match.group(1),
                "methods": [],
                "docstring": ""
            }
            classes.append(current_class)
            continue

        func_match = func_pattern.search(line_stripped)
        if func_match:
            func_name = func_match.group(1)
            args = [a.strip() for a in func_match.group(2).split(",") if a.strip()]
            if current_class and "{" in line_stripped and "function" not in line_stripped:
                current_class["methods"].append({"name": func_name, "args": args, "docstring": ""})
            else:
                functions.append({"name": func_name, "args": args, "docstring": ""})
            continue

        arrow_match = arrow_pattern.search(line_stripped)
        if arrow_match:
            functions.append({
                "name": arrow_match.group(1),
                "args": [],
                "docstring": ""
            })

    return {"classes": classes, "functions": functions}


def generate_file_map(file_path: str) -> dict:
    """Parse any supported file format and return structured layout."""
    if file_path.endswith(".py"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                source = f.read()
            return _parse_python_source(source, file_path)
        except Exception as e:
            return {"error": str(e)}
    elif file_path.endswith(".ipynb"):
        return _parse_ipynb_file(file_path)
    elif file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
        return _parse_js_ts_file(file_path)
    return {}


def format_code_map_text(project_root: str) -> str:
    """Scan directory recursively and print code map in indented tree layout."""
    import sys
    py_files, js_files, _ = _find_all_files(project_root)
    all_files = sorted(py_files + js_files)
    
    output = []
    for f in all_files:
        try:
            rel_path = os.path.relpath(f, project_root).replace("\\", "/")
        except ValueError:
            rel_path = f
            
        data = generate_file_map(f)
        if not data or "error" in data:
            continue
            
        classes = data.get("classes", [])
        functions = data.get("functions", [])
        
        if not classes and not functions:
            continue
            
        output.append(f"{rel_path}")
        
        for cls in classes:
            doc = f" - # {cls['docstring']}" if cls.get("docstring") else ""
            output.append(f"  class {cls['name']}{doc}")
            for m in cls.get("methods", []):
                args_str = ", ".join(m["args"])
                doc_m = f" - # {m['docstring']}" if m.get("docstring") else ""
                output.append(f"    def {m['name']}({args_str}){doc_m}")
                
        for func in functions:
            args_str = ", ".join(func["args"])
            doc_f = f" - # {func['docstring']}" if func.get("docstring") else ""
            output.append(f"  def {func['name']}({args_str}){doc_f}")
            
    text = "\n".join(output)
    # Sanitize for console safety
    text = text.replace("→", "->")
    encoding = sys.stdout.encoding or "ascii"
    try:
        return text.encode(encoding, errors="replace").decode(encoding)
    except Exception:
        return text.encode("ascii", errors="replace").decode("ascii")
