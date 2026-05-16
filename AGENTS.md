# Agent Instructions for Hermes PR Investigator

## Project Context

This is a **Hermes Agent skill** for the DEV Hermes Agent Challenge 2026. The skill extends Hermes Agent with autonomous pull request investigation capabilities.

## Build & Development

No build step required — skills are interpreted by Hermes Agent at runtime. However, helper scripts should be tested independently.

### Testing Scripts

```bash
# Test diff analyzer
cd skills/devops/pr-investigator/scripts
python3 analyze_diff.py --plan test.diff

# Test dependency tracer
python3 trace_deps.py src/main.py ../../..

# Test report generator
python3 generate_report.py --pr-data test_pr.json --findings test_findings.json
```

### Installing Locally

```bash
bash install.sh
```

## Architecture Decisions

- **Skill-based, not plugin**: Skills are easier to install and share than plugins. No Python code runs inside Hermes — only shell commands and existing tools.
- **Helper scripts in Python/bash**: Hermes calls these via `terminal` tool. They output JSON for structured consumption.
- **State in `.hermes/pr-data/`**: Follows Hermes conventions for session-scoped data.
- **JSON intermediate format**: Scripts output JSON; Hermes parses and reasons about it.

## Coding Style

- Scripts should be defensive (check for missing env vars, handle errors)
- Output valid JSON to stdout
- Log errors to stderr
- Support both local and GitHub PR workflows
- No external dependencies beyond stdlib + curl

## Submission Checklist

- [ ] SKILL.md follows Hermes skill format with proper frontmatter
- [ ] Scripts are executable and tested
- [ ] README explains what, why, and how
- [ ] Demo data included
- [ ] Installation script works
- [ ] DEV post written and published
