#!/usr/bin/env python3
"""
trace_deps.py - Trace upstream and downstream dependencies for a file
Usage: python3 trace_deps.py <file_path> <repo_root>
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def find_imports(file_path: str, repo_root: str) -> dict:
    """Find files that import the target file and files the target imports."""
    target_path = Path(file_path).resolve()
    repo_path = Path(repo_root).resolve()
    
    if not target_path.exists():
        return {"error": f"File not found: {file_path}"}
    
    # Get module name from file path
    try:
        rel_path = target_path.relative_to(repo_path)
    except ValueError:
        return {"error": f"File {file_path} is not inside repo {repo_root}"}
    
    # Possible module names
    module_variants = []
    
    # Python: foo/bar/baz.py -> foo.bar.baz, foo.bar, bar.baz, baz
    if target_path.suffix == '.py':
        parts = list(rel_path.with_suffix('').parts)
        module_variants.append('.'.join(parts))
        if len(parts) > 1:
            module_variants.append('.'.join(parts[-2:]))
        module_variants.append(parts[-1])
    
    # JS/TS: foo/bar/baz.js -> foo/bar/baz, ./foo/bar/baz, baz
    if target_path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
        parts = list(rel_path.with_suffix('').parts)
        module_variants.append('/'.join(parts))
        module_variants.append('./' + '/'.join(parts))
        module_variants.append(target_path.stem)
    
    upstream = []  # Files that import target
    downstream = []  # Files that target imports
    
    # Read target file to find its imports
    try:
        with open(target_path, 'r', encoding='utf-8', errors='replace') as f:
            target_content = f.read()
    except Exception as e:
        return {"error": f"Cannot read file: {e}"}
    
    # Python imports in target
    py_imports = re.findall(
        r'^(?:from|import)\s+([\w.]+)',
        target_content,
        re.MULTILINE
    )
    
    # JS/TS imports in target
    js_imports = re.findall(
        r"import\s+.*?\s+from\s+['\"](.+?)['\"]|require\(['\"](.+?)['\"]\)",
        target_content
    )
    js_imports = [i[0] or i[1] for i in js_imports if i[0] or i[1]]
    
    # Search repo for files that import the target
    for root, dirs, files in os.walk(repo_path):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {
            'node_modules', 'venv', '.venv', '__pycache__', '.git',
            'dist', 'build', '.hermes', '.pytest_cache', '.mypy_cache'
        }]
        
        for filename in files:
            if not filename.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                continue
            
            filepath = Path(root) / filename
            if filepath == target_path:
                continue
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception:
                continue
            
            # Check if this file imports the target
            for mod in module_variants:
                if filename.endswith('.py'):
                    patterns = [
                        rf'\bfrom\s+{re.escape(mod)}\b',
                        rf'\bimport\s+{re.escape(mod)}\b',
                    ]
                else:
                    patterns = [
                        rf"from\s+['\"].*?{re.escape(mod)}['\"]",
                        rf"require\(['\"].*?{re.escape(mod)}['\"]\)",
                        rf"import\s+.*?{re.escape(mod)}",
                    ]
                
                if any(re.search(p, content) for p in patterns):
                    try:
                        rel = filepath.relative_to(repo_path)
                        upstream.append(str(rel))
                    except ValueError:
                        upstream.append(str(filepath))
                    break
    
    return {
        "target_file": str(rel_path),
        "module_names": module_variants,
        "upstream_importers": list(set(upstream))[:20],  # Limit to 20
        "target_imports": {
            "python": py_imports[:20],
            "javascript": js_imports[:20]
        }
    }


def main():
    parser = argparse.ArgumentParser(description='Trace file dependencies')
    parser.add_argument('file_path', help='Path to the file to analyze')
    parser.add_argument('repo_root', help='Path to the repository root')
    args = parser.parse_args()
    
    result = find_imports(args.file_path, args.repo_root)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
