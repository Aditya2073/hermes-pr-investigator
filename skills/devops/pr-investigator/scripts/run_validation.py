#!/usr/bin/env python3
"""
run_validation.py - Run tests, lint, and type checks on changed files
Usage: python3 run_validation.py --files <file1> <file2> ... [--repo-root <path>]
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def detect_project_type(repo_root: str) -> str:
    """Detect the type of project."""
    root = Path(repo_root)
    if (root / 'package.json').exists():
        return 'node'
    if any((root / f).exists() for f in ['setup.py', 'pyproject.toml', 'requirements.txt', 'Pipfile']):
        return 'python'
    if (root / 'Cargo.toml').exists():
        return 'rust'
    if (root / 'go.mod').exists():
        return 'go'
    return 'unknown'


def run_command(cmd: list, cwd: str, timeout: int = 300) -> dict:
    """Run a shell command and return structured output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "command": ' '.join(cmd),
            "returncode": result.returncode,
            "stdout": result.stdout[:5000],  # Limit output
            "stderr": result.stderr[:5000],
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {
            "command": ' '.join(cmd),
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds",
            "success": False
        }
    except FileNotFoundError:
        return {
            "command": ' '.join(cmd),
            "returncode": -1,
            "stdout": "",
            "stderr": f"Command not found: {cmd[0]}",
            "success": False
        }


def get_python_cmd() -> str:
    """Find the Python command."""
    for cmd in ['python3', 'python']:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
            return cmd
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    return 'python3'


def run_python_tests(repo_root: str, changed_files: list, timeout: int) -> dict:
    """Run Python tests."""
    results = {}
    python_cmd = get_python_cmd()
    
    # Try pytest first
    if any(Path(repo_root).glob('**/pytest.ini')) or any(Path(repo_root).glob('**/setup.cfg')) or any(Path(repo_root).glob('**/pyproject.toml')):
        cmd = [python_cmd, '-m', 'pytest', '-v', '--tb=short']
        # Add specific test files if we can map them
        test_files = []
        for f in changed_files:
            base = Path(f).stem
            for pattern in [f'test_{base}.py', f'{base}_test.py', f'tests/test_{base}.py']:
                matches = list(Path(repo_root).rglob(pattern))
                if matches:
                    test_files.extend([str(m.relative_to(repo_root)) for m in matches])
        
        if test_files:
            cmd.extend(list(set(test_files)))
        else:
            cmd.append('.')
        
        results['pytest'] = run_command(cmd, repo_root, timeout)
    else:
        results['pytest'] = {"skipped": True, "reason": "pytest not configured"}
    
    # Try unittest
    if any('test' in f for f in changed_files):
        cmd = [python_cmd, '-m', 'unittest', 'discover', '-s', 'tests', '-v']
        results['unittest'] = run_command(cmd, repo_root, timeout)
    
    return results


def run_node_tests(repo_root: str, changed_files: list, timeout: int) -> dict:
    """Run Node.js tests."""
    results = {}
    
    package_json = Path(repo_root) / 'package.json'
    if package_json.exists():
        with open(package_json) as f:
            import json
            pkg = json.load(f)
        scripts = pkg.get('scripts', {})
        
        if 'test' in scripts:
            results['npm_test'] = run_command(['npm', 'test'], repo_root, timeout)
        else:
            results['npm_test'] = {"skipped": True, "reason": "No test script in package.json"}
    
    return results


def run_lint(repo_root: str, project_type: str, changed_files: list) -> dict:
    """Run linting."""
    results = {}
    
    if project_type == 'python':
        if any(Path(repo_root).glob('**/.flake8')) or any(Path(repo_root).glob('**/setup.cfg')):
            results['flake8'] = run_command(['flake8'] + changed_files, repo_root)
        
        if (Path(repo_root) / 'pyproject.toml').exists():
            results['ruff'] = run_command(['ruff', 'check'] + changed_files, repo_root)
        
        if any(Path(repo_root).glob('**/.pylintrc')):
            results['pylint'] = run_command(['pylint'] + changed_files, repo_root)
    
    elif project_type == 'node':
        package_json = Path(repo_root) / 'package.json'
        if package_json.exists():
            with open(package_json) as f:
                import json
                pkg = json.load(f)
            scripts = pkg.get('scripts', {})
            
            if 'lint' in scripts:
                results['npm_lint'] = run_command(['npm', 'run', 'lint'], repo_root)
            elif 'eslint' in str(pkg.get('devDependencies', {})):
                results['eslint'] = run_command(['npx', 'eslint'] + changed_files, repo_root)
    
    return results


def run_type_check(repo_root: str, project_type: str) -> dict:
    """Run type checking."""
    results = {}
    
    if project_type == 'python':
        if (Path(repo_root) / 'pyproject.toml').exists() or any(Path(repo_root).glob('**/setup.cfg')):
            results['mypy'] = run_command(['mypy', '.'], repo_root)
    
    elif project_type == 'node':
        if (Path(repo_root) / 'tsconfig.json').exists():
            results['tsc'] = run_command(['npx', 'tsc', '--noEmit'], repo_root)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Run validation on changed files')
    parser.add_argument('--files', nargs='+', required=True, help='Changed files')
    parser.add_argument('--repo-root', default='.', help='Repository root')
    parser.add_argument('--timeout', type=int, default=300, help='Test timeout in seconds')
    args = parser.parse_args()
    
    repo_root = os.path.abspath(args.repo_root)
    project_type = detect_project_type(repo_root)
    
    result = {
        "project_type": project_type,
        "repo_root": repo_root,
        "changed_files": args.files,
        "tests": {},
        "lint": {},
        "type_check": {}
    }
    
    if project_type == 'python':
        result['tests'] = run_python_tests(repo_root, args.files, args.timeout)
    elif project_type == 'node':
        result['tests'] = run_node_tests(repo_root, args.files, args.timeout)
    else:
        result['tests'] = {"skipped": True, "reason": f"Unknown project type: {project_type}"}
    
    result['lint'] = run_lint(repo_root, project_type, args.files)
    result['type_check'] = run_type_check(repo_root, project_type)
    
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
