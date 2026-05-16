#!/usr/bin/env python3
"""
generate_report.py - Generate a structured markdown report from investigation findings
Usage: python3 generate_report.py --pr-data <pr.json> --findings <findings.json> [--output <path>]
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def load_json(path: str) -> dict:
    """Load JSON file or return empty dict."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def severity_emoji(severity: str) -> str:
    """Get emoji for severity level."""
    return {
        "Critical": "🚨",
        "High": "⚠️",
        "Medium": "💡",
        "Low": "📝",
        "Info": "ℹ️"
    }.get(severity, "📝")


def generate_markdown_report(pr_data: dict, findings: dict, diff_summary: dict = None) -> str:
    """Generate a comprehensive markdown report."""
    
    pr_number = pr_data.get('number', 'N/A')
    pr_title = pr_data.get('title', 'Unknown PR')
    pr_url = pr_data.get('html_url', '')
    author = pr_data.get('user', {}).get('login', 'Unknown')
    created_at = pr_data.get('created_at', '')
    body = pr_data.get('body', '') or ''
    
    files_changed = pr_data.get('changed_files', 0)
    additions = pr_data.get('additions', 0)
    deletions = pr_data.get('deletions', 0)
    
    # Risk assessment
    risk = findings.get('risk_assessment', {})
    risk_level = risk.get('risk_level', 'Unknown')
    risk_findings = risk.get('findings', [])
    
    # Validation
    validation = findings.get('validation', {})
    
    # Custom findings
    custom_findings = findings.get('custom_findings', [])
    
    # Group findings by severity
    by_severity = {"Critical": [], "High": [], "Medium": [], "Low": [], "Info": []}
    for f in risk_findings + custom_findings:
        sev = f.get('severity', 'Info')
        by_severity.setdefault(sev, []).append(f)
    
    # Build report
    lines = []
    lines.append(f"# PR Investigation Report: {pr_title}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| **PR** | [#{pr_number}]({pr_url}) |")
    lines.append(f"| **Author** | @{author} |")
    lines.append(f"| **Created** | {created_at} |")
    lines.append(f"| **Files Changed** | {files_changed} |")
    lines.append(f"| **Additions** | +{additions} |")
    lines.append(f"| **Deletions** | -{deletions} |")
    lines.append(f"| **Overall Risk** | **{risk_level}** |")
    lines.append("")
    
    # PR Description summary
    if body:
        body_summary = body[:500] + "..." if len(body) > 500 else body
        lines.append("## PR Description")
        lines.append("")
        lines.append(body_summary)
        lines.append("")
    
    # Findings
    lines.append("## Findings")
    lines.append("")
    
    total_findings = sum(len(v) for v in by_severity.values())
    if total_findings == 0:
        lines.append("✅ No issues detected during automated investigation.")
        lines.append("")
    else:
        for severity in ["Critical", "High", "Medium", "Low", "Info"]:
            items = by_severity.get(severity, [])
            if not items:
                continue
            
            lines.append(f"### {severity_emoji(severity)} {severity} ({len(items)})")
            lines.append("")
            
            for i, finding in enumerate(items, 1):
                prefix = f"{severity[0]}-{i}"
                msg = finding.get('message', 'No details')
                suggestion = finding.get('suggestion', '')
                category = finding.get('category', 'General')
                file_ref = finding.get('file', '')
                
                lines.append(f"**[{prefix}]** {msg}")
                if file_ref:
                    lines.append(f"- **Location**: `{file_ref}`")
                lines.append(f"- **Category**: {category}")
                if suggestion:
                    lines.append(f"- **Suggestion**: {suggestion}")
                lines.append("")
    
    # Validation Results
    lines.append("## Validation Results")
    lines.append("")
    
    if validation:
        tests = validation.get('tests', {})
        lint = validation.get('lint', {})
        type_check = validation.get('type_check', {})
        
        # Tests
        test_results = []
        for tool, result in tests.items():
            if isinstance(result, dict):
                if result.get('skipped'):
                    status = "⏭️ Skipped"
                elif result.get('success'):
                    status = "✅ Passed"
                else:
                    status = "❌ Failed"
                test_results.append(f"- **{tool}**: {status}")
        
        if test_results:
            lines.append("### Tests")
            lines.extend(test_results)
            lines.append("")
        else:
            lines.append("### Tests")
            lines.append("- No test results available")
            lines.append("")
        
        # Lint
        lint_results = []
        for tool, result in lint.items():
            if isinstance(result, dict):
                if result.get('skipped'):
                    status = "⏭️ Skipped"
                elif result.get('success'):
                    status = "✅ Passed"
                else:
                    status = "❌ Failed"
                lint_results.append(f"- **{tool}**: {status}")
        
        if lint_results:
            lines.append("### Lint")
            lines.extend(lint_results)
            lines.append("")
        
        # Type Check
        type_results = []
        for tool, result in type_check.items():
            if isinstance(result, dict):
                if result.get('skipped'):
                    status = "⏭️ Skipped"
                elif result.get('success'):
                    status = "✅ Passed"
                else:
                    status = "❌ Failed"
                type_results.append(f"- **{tool}**: {status}")
        
        if type_results:
            lines.append("### Type Check")
            lines.extend(type_results)
            lines.append("")
    else:
        lines.append("No validation data available.")
        lines.append("")
    
    # Diff Summary
    if diff_summary:
        lines.append("## Change Summary")
        lines.append("")
        lines.append(f"- **Total files**: {diff_summary.get('total_files', 'N/A')}")
        lines.append(f"- **Test files changed**: {diff_summary.get('test_files_changed', 'N/A')}")
        lines.append(f"- **Core files changed**: {diff_summary.get('core_files_changed', 'N/A')}")
        lines.append(f"- **Config files changed**: {diff_summary.get('config_files_changed', 'N/A')}")
        lines.append("")
        
        top_files = diff_summary.get('top_changed_files', [])
        if top_files:
            lines.append("### Most Changed Files")
            lines.append("")
            lines.append("| File | Additions | Deletions |")
            lines.append("|------|-----------|-----------|")
            for f in top_files:
                lines.append(f"| `{f['path']}` | +{f['additions']} | -{f['deletions']} |")
            lines.append("")
    
    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    
    recommendations = findings.get('recommendations', [])
    if not recommendations:
        # Auto-generate from findings
        if risk_level in ['Critical', 'High']:
            recommendations.append("Address Critical/High severity findings before merging")
        if diff_summary and diff_summary.get('test_files_changed', 0) == 0 and diff_summary.get('total_files', 0) > 1:
            recommendations.append("Consider adding tests for the changed functionality")
        if files_changed > 20:
            recommendations.append("Large PR - consider breaking into smaller changes for easier review")
        if not recommendations:
            recommendations.append("No specific recommendations - PR looks good for further human review")
    
    for i, rec in enumerate(recommendations, 1):
        lines.append(f"{i}. {rec}")
    lines.append("")
    
    # Investigation Log
    lines.append("## Investigation Log")
    lines.append("")
    investigation = findings.get('investigation_log', [])
    for entry in investigation:
        status = "✅" if entry.get('completed') else "⏳"
        lines.append(f"- {status} {entry.get('phase', 'Unknown')}")
    lines.append("")
    
    # Footer
    lines.append("---")
    lines.append(f"*Report generated by Hermes PR Investigator at {datetime.now().isoformat()}*")
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Generate PR investigation report')
    parser.add_argument('--pr-data', required=True, help='Path to PR metadata JSON')
    parser.add_argument('--findings', required=True, help='Path to findings JSON')
    parser.add_argument('--diff-summary', help='Path to diff summary JSON')
    parser.add_argument('--output', help='Output file path')
    args = parser.parse_args()
    
    pr_data = load_json(args.pr_data)
    findings = load_json(args.findings)
    diff_summary = load_json(args.diff_summary) if args.diff_summary else None
    
    report = generate_markdown_report(pr_data, findings, diff_summary)
    
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(json.dumps({"success": True, "output": args.output}))
    else:
        print(report)


if __name__ == '__main__':
    main()
