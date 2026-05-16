# Hermes PR Investigator

> An autonomous pull request investigation skill for [Hermes Agent](https://hermes-agent.nousresearch.com/) that plans, executes, and reports comprehensive code reviews using multi-step agentic reasoning.

[![Hermes Agent](https://img.shields.io/badge/Built%20with-Hermes%20Agent-blue)](https://hermes-agent.nousresearch.com/)
[![Challenge](https://img.shields.io/badge/DEV%20Challenge-Hermes%20Agent%202026-green)](https://dev.to/challenges/hermes-agent-2026-05-15)

## What It Does

Most AI code review tools are static diff summarizers — they read the patch once and spit out generic comments. **Hermes PR Investigator** is different. It's an agentic skill that turns Hermes Agent into an autonomous PR reviewer that:

1. **Plans an investigation strategy** based on the PR's scope, changed files, and risk profile
2. **Reads modified files** and traces upstream/downstream dependencies
3. **Runs validation** — tests, lint, type checks — on the actual code
4. **Cross-references** the codebase for affected patterns and security anti-patterns
5. **Generates a structured report** with severity ratings and actionable fixes

### Key Capabilities

- **Multi-phase agentic workflow**: Discovery → Deep Analysis → Validation → Cross-Reference → Report
- **Risk scoring**: Automatically identifies high-risk changes (auth code, core modules, large deletions)
- **Dependency tracing**: Finds which files import changed modules and vice versa
- **Test gap detection**: Flags large changes without corresponding test updates
- **Security scanning**: Detects auth modifications, env changes, and common anti-patterns
- **Structured reporting**: Generates markdown reports with severity ratings and recommendations

## Installation

### Prerequisites

- [Hermes Agent](https://hermes-agent.nousresearch.com/docs/getting-started/installation) installed
- GitHub Personal Access Token with `repo` scope

### Quick Install

```bash
git clone https://github.com/yourusername/hermes-pr-investigator.git
cd hermes-pr-investigator
bash install.sh
```

Or manually copy the skill:

```bash
cp -r skills/devops/pr-investigator ~/.hermes/skills/devops/pr-investigator
```

### Configuration

Add your GitHub token to `~/.hermes/.env`:

```bash
echo 'GITHUB_TOKEN=ghp_xxxxxxxxxxxx' >> ~/.hermes/.env
```

Optional config in `~/.hermes/config.yaml`:

```yaml
skills:
  config:
    pr_investigator:
      default_repo: "myorg/myrepo"
      max_files_to_read: 20
      test_timeout: 300
      report_format: markdown
```

## Usage

### In Hermes CLI

```bash
# Start Hermes with skills
hermes chat --toolsets skills

# Use the slash command
/pr-investigator https://github.com/owner/repo/pull/123

# With focus mode
/pr-investigator https://github.com/owner/repo/pull/456 --focus security

# Local branch review
/pr-investigator local --branch feature/auth-refactor
```

### In Natural Language

```
"Investigate PR https://github.com/nousresearch/hermes-agent/pull/42"
"Review this branch for security issues"
"Deep-dive into PR #123 and check for missing tests"
```

## How It Works

### Phase 1: Discovery & Planning

The skill fetches PR metadata and diff from GitHub API, then runs `analyze_diff.py` to generate an investigation plan. Hermes Agent uses its `todo` tool to track progress across phases.

### Phase 2: Deep File Analysis

Hermes reads each modified file using its built-in `read_file` tool. For high-risk files, it runs `trace_deps.py` to find upstream importers and downstream dependencies.

### Phase 3: Validation

The `run_validation.py` script detects the project type (Python, Node, Rust, Go) and runs appropriate tests, linting, and type checking.

### Phase 4: Cross-Reference

Hermes searches the codebase for patterns affected by the changes and checks for documentation updates.

### Phase 5: Report Generation

`generate_report.py` compiles all findings into a structured markdown report with severity ratings.

## Project Structure

```
hermes-pr-investigator/
├── skills/devops/pr-investigator/
│   ├── SKILL.md                    # Main skill instructions
│   ├── scripts/
│   │   ├── fetch_pr.sh            # GitHub API PR fetcher
│   │   ├── analyze_diff.py        # Diff parser & risk analyzer
│   │   ├── trace_deps.py          # Dependency tracer
│   │   ├── run_validation.py      # Test/lint/type runner
│   │   └── generate_report.py     # Report generator
│   └── templates/
│       └── report_template.md     # Report template
├── demo/                          # Demo environment
├── install.sh                     # One-line installer
└── README.md                      # This file
```

## Demo

See the `demo/` directory for a sample repository and example investigation output.

```bash
cd demo/sample-repo
# Create a test PR scenario
git checkout -b feature/add-validation
git apply ../sample-diff.patch
# Then run the investigator on this branch
```

## Why Hermes Agent?

This skill leverages Hermes Agent's unique capabilities:

- **Planning & reasoning**: Hermes creates investigation plans and adapts them based on findings
- **Tool orchestration**: Seamlessly chains terminal, file, web, and code execution tools
- **Progressive disclosure**: Skill loads on-demand, keeping token usage efficient
- **Skills ecosystem**: Follows the open `agentskills.io` standard for portability
- **Memory**: Learns from previous reviews to improve over time

## Contributing

Contributions welcome! This is a skill, not a core tool, so you can extend it by:

1. Editing `SKILL.md` to add new investigation phases
2. Adding scripts to `scripts/` for new analysis types
3. Submitting PRs with improvements

## License

MIT License — see LICENSE file for details.

---

*Built for the [DEV Hermes Agent Challenge 2026](https://dev.to/challenges/hermes-agent-2026-05-15)*
