#!/usr/bin/env python3
"""
analyze_diff.py - Parse git diffs and generate investigation plans
Usage:
  python3 analyze_diff.py --plan <diff.patch>          # Output investigation plan
  python3 analyze_diff.py --summary <diff.patch>       # Output change summary
  python3 analyze_diff.py --risk <diff.patch>          # Output risk assessment
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class FileChange:
    path: str
    status: str  # added, modified, removed
    additions: int
    deletions: int
    is_test: bool
    is_config: bool
    is_core: bool
    risk_score: int  # 0-100


@dataclass
class InvestigationPlan:
    total_files: int
    total_additions: int
    total_deletions: int
    risk_level: str  # Low, Medium, High, Critical
    focus_files: List[str]
    phases: List[dict]


def parse_diff(diff_path: str) -> List[FileChange]:
    """Parse a unified diff file and extract file changes."""
    changes = []
    
    try:
        with open(diff_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except FileNotFoundError:
        print(json.dumps({"error": f"Diff file not found: {diff_path}"}), file=sys.stderr)
        sys.exit(1)
    
    # Parse diff headers
    # Unified diff format: --- a/path and +++ b/path
    file_blocks = re.split(r'(?=diff --git )', content)
    
    for block in file_blocks:
        if not block.strip():
            continue
            
        # Extract file path
        match = re.search(r'diff --git a/(.+?) b/(.+?)(?:\n|$)', block)
        if not match:
            continue
            
        old_path = match.group(1)
        new_path = match.group(2)
        path = new_path if new_path != '/dev/null' else old_path
        
        # Determine status
        if old_path == '/dev/null':
            status = 'added'
        elif new_path == '/dev/null':
            status = 'removed'
        else:
            status = 'modified'
        
        # Count additions and deletions
        additions = len(re.findall(r'\n\+', block)) - len(re.findall(r'\n\+\+\+', block))
        deletions = len(re.findall(r'\n-', block)) - len(re.findall(r'\n---', block))
        
        # Classify file
        is_test = bool(re.search(r'(test|spec|__tests__)', path, re.I))
        is_config = bool(re.search(r'(\.json|\.yaml|\.yml|\.toml|\.ini|config|\.env)', path, re.I))
        is_core = bool(re.search(r'(src/|lib/|app/|core/|main\.|index\.)', path, re.I))
        
        # Calculate risk score
        risk_score = 0
        if status == 'removed':
            risk_score += 30
        if status == 'added' and is_core:
            risk_score += 20
        if additions + deletions > 100:
            risk_score += 20
        if is_core:
            risk_score += 20
        if not is_test and additions > 0 and 'test' not in path.lower():
            # Check if tests were added for this change
            risk_score += 10
        
        risk_score = min(100, risk_score)
        
        changes.append(FileChange(
            path=path,
            status=status,
            additions=max(0, additions),
            deletions=max(0, deletions),
            is_test=is_test,
            is_config=is_config,
            is_core=is_core,
            risk_score=risk_score
        ))
    
    return changes


def generate_plan(changes: List[FileChange]) -> InvestigationPlan:
    """Generate an investigation plan from parsed changes."""
    total_files = len(changes)
    total_additions = sum(c.additions for c in changes)
    total_deletions = sum(c.deletions for c in changes)
    
    # Calculate overall risk
    avg_risk = sum(c.risk_score for c in changes) / len(changes) if changes else 0
    max_risk = max((c.risk_score for c in changes), default=0)
    
    if max_risk >= 80 or avg_risk >= 60:
        risk_level = 'Critical'
    elif max_risk >= 60 or avg_risk >= 40:
        risk_level = 'High'
    elif max_risk >= 40 or avg_risk >= 25:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'
    
    # Identify focus files (top 10 by risk score)
    sorted_changes = sorted(changes, key=lambda c: c.risk_score, reverse=True)
    focus_files = [c.path for c in sorted_changes[:10]]
    
    # Generate phases
    phases = [
        {
            "name": "Discovery & Planning",
            "tasks": [
                f"Review {total_files} changed files",
                f"Identify {len(focus_files)} high-risk files for deep analysis"
            ],
            "estimated_time": "2-3 minutes"
        },
        {
            "name": "Deep File Analysis",
            "tasks": [
                f"Read and analyze top {min(10, len(focus_files))} focus files",
                "Trace upstream and downstream dependencies",
                "Identify public API surface changes"
            ],
            "estimated_time": "5-10 minutes"
        },
        {
            "name": "Validation",
            "tasks": [
                "Check for missing tests",
                "Run test suite on changed areas",
                "Run linting and type checking"
            ],
            "estimated_time": "3-5 minutes"
        },
        {
            "name": "Cross-Reference",
            "tasks": [
                "Search for affected patterns",
                "Check documentation needs",
                "Look for security anti-patterns"
            ],
            "estimated_time": "2-3 minutes"
        },
        {
            "name": "Report Generation",
            "tasks": [
                "Compile findings",
                "Assign severity ratings",
                "Generate structured report"
            ],
            "estimated_time": "1-2 minutes"
        }
    ]
    
    return InvestigationPlan(
        total_files=total_files,
        total_additions=total_additions,
        total_deletions=total_deletions,
        risk_level=risk_level,
        focus_files=focus_files,
        phases=phases
    )


def generate_summary(changes: List[FileChange]) -> dict:
    """Generate a human-readable summary of changes."""
    test_files = [c for c in changes if c.is_test]
    config_files = [c for c in changes if c.is_config]
    core_files = [c for c in changes if c.is_core]
    added_files = [c for c in changes if c.status == 'added']
    removed_files = [c for c in changes if c.status == 'removed']
    
    return {
        "total_files": len(changes),
        "total_additions": sum(c.additions for c in changes),
        "total_deletions": sum(c.deletions for c in changes),
        "test_files_changed": len(test_files),
        "config_files_changed": len(config_files),
        "core_files_changed": len(core_files),
        "files_added": len(added_files),
        "files_removed": len(removed_files),
        "top_changed_files": [
            {"path": c.path, "additions": c.additions, "deletions": c.deletions}
            for c in sorted(changes, key=lambda c: c.additions + c.deletions, reverse=True)[:5]
        ]
    }


def generate_risk_assessment(changes: List[FileChange]) -> dict:
    """Generate a risk assessment."""
    findings = []
    
    # Check for large changes without tests
    for c in changes:
        if c.additions + c.deletions > 50 and not c.is_test and not any(t.path == c.path.replace('.py', '_test.py') for t in changes if t.is_test):
            findings.append({
                "severity": "Medium",
                "category": "Test Coverage",
                "message": f"Large change in {c.path} without corresponding test updates",
                "suggestion": "Add or update tests for this change"
            })
    
    # Check for removed files
    for c in changes:
        if c.status == 'removed' and c.is_core:
            findings.append({
                "severity": "High",
                "category": "Breaking Change",
                "message": f"Core file removed: {c.path}",
                "suggestion": "Verify no downstream consumers depend on this file"
            })
    
    # Check for config changes
    for c in changes:
        if c.is_config and 'env' in c.path.lower():
            findings.append({
                "severity": "High",
                "category": "Security",
                "message": f"Environment config changed: {c.path}",
                "suggestion": "Review for accidentally committed secrets"
            })
    
    # Check for auth-related changes
    for c in changes:
        if re.search(r'(auth|password|token|secret|credential|permission)', c.path, re.I):
            findings.append({
                "severity": "High",
                "category": "Security",
                "message": f"Authentication-related file modified: {c.path}",
                "suggestion": "Ensure security best practices are followed"
            })
    
    risk_level = "Low"
    if any(f["severity"] == "Critical" for f in findings):
        risk_level = "Critical"
    elif any(f["severity"] == "High" for f in findings):
        risk_level = "High"
    elif any(f["severity"] == "Medium" for f in findings):
        risk_level = "Medium"
    
    return {
        "risk_level": risk_level,
        "findings_count": len(findings),
        "findings": findings
    }


def main():
    parser = argparse.ArgumentParser(description='Analyze git diffs for PR investigation')
    parser.add_argument('diff_path', help='Path to the diff patch file')
    parser.add_argument('--plan', action='store_true', help='Generate investigation plan')
    parser.add_argument('--summary', action='store_true', help='Generate change summary')
    parser.add_argument('--risk', action='store_true', help='Generate risk assessment')
    args = parser.parse_args()
    
    changes = parse_diff(args.diff_path)
    
    if not changes:
        print(json.dumps({"error": "No changes found in diff"}))
        sys.exit(1)
    
    if args.plan:
        plan = generate_plan(changes)
        print(json.dumps(asdict(plan), indent=2))
    elif args.summary:
        summary = generate_summary(changes)
        print(json.dumps(summary, indent=2))
    elif args.risk:
        risk = generate_risk_assessment(changes)
        print(json.dumps(risk, indent=2))
    else:
        # Default: output all
        plan = generate_plan(changes)
        summary = generate_summary(changes)
        risk = generate_risk_assessment(changes)
        print(json.dumps({
            "plan": asdict(plan),
            "summary": summary,
            "risk": risk
        }, indent=2))


if __name__ == '__main__':
    main()
