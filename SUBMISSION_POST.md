---
title: "I Built an Agent That Actually Reviews Your Pull Requests"
published: false
tags: hermesagentchallenge, devchallenge, agents, code-review, automation
---

*This is a submission for the [Hermes Agent Challenge](https://dev.to/challenges/hermes-agent-2026-05-15)*

## The Problem with AI Code Review

Every AI coding tool on the market can summarize a diff. "This PR adds 5 files and modifies authentication." Great — but that's not a review. That's a description.

A real code review requires:
- **Reading the actual files** to understand context, not just the diff
- **Tracing dependencies** to see who consumes changed code
- **Running tests** to verify nothing broke
- **Searching for patterns** that might be affected
- **Thinking in phases**, not blasting out generic comments

In other words: a real review requires **agency**.

## What I Built

**Hermes PR Investigator** is a custom skill for [Hermes Agent](https://hermes-agent.nousresearch.com/) that turns the agent into an autonomous PR reviewer. It doesn't summarize diffs — it *investigates* them through a 5-phase agentic workflow.

### The 5-Phase Investigation

```
Discovery & Planning
        ↓
Deep File Analysis
        ↓
Validation (tests, lint, type-check)
        ↓
Cross-Reference (patterns, docs, security)
        ↓
Structured Report Generation
```

### How It's Different

| Static Diff Summarizer | Hermes PR Investigator |
|------------------------|------------------------|
| Reads patch once | Reads full files and traces dependencies |
| Generic comments | Risk-scored, severity-rated findings |
| No validation | Runs tests, lint, type checks |
| Surface-level | Cross-references codebase for affected patterns |
| Static output | Agent adapts investigation based on findings |

## Demo

Here's what happens when I point it at a PR adding authentication middleware:

### Phase 1: Discovery

Hermes fetches the PR metadata and runs the diff analyzer:

```
hermes chat --toolsets skills -q "/pr-investigator https://github.com/demo/repo/pull/42"
```

The `analyze_diff.py` script parses the patch, scores each file by risk, and generates an investigation plan. Hermes creates todos to track progress.

### Phase 2: Deep File Analysis

Hermes reads each modified file using its built-in `read_file` tool. For the auth middleware, it also runs `trace_deps.py`:

```bash
python3 trace_deps.py src/middleware/auth.py .
```

Output:
```json
{
  "target_file": "src/middleware/auth.py",
  "upstream_importers": ["src/routes/login.py", "src/app.py"],
  "target_imports": {
    "python": ["jwt", "os", "functools", "flask"]
  }
}
```

### Phase 3: Validation

`run_validation.py` auto-detects the project type and runs pytest:

```
Tests: ❌ Failed (2 failures in auth tests)
Lint: ✅ Passed
Type Check: ✅ Passed
```

### Phase 4: Cross-Reference

Hermes searches for security anti-patterns and finds that the default JWT secret is hardcoded as a fallback.

### Phase 5: Report

The final output is a structured markdown report posted as a PR comment:

---

## 🔍 PR Investigation Report: Add user authentication middleware

| Field | Value |
|-------|-------|
| **Overall Risk** | **High** |
| **Files Changed** | 5 |

### ⚠️ High Findings

**[H-1]** Core file modified with auth logic but no tests added
- **Suggestion**: Add tests for expired tokens, malformed tokens, missing headers

**[H-2]** Environment config changed: `.env.example`
- **Suggestion**: Review for accidentally committed secrets

### Recommendations

1. Address high-severity findings before merging
2. Add tests for token validation edge cases
3. Ensure JWT_SECRET is rotated and not in version control

---

## Code

**Repository**: [github.com/yourusername/hermes-pr-investigator](https://github.com/yourusername/hermes-pr-investigator)

### Project Structure

```
hermes-pr-investigator/
├── skills/devops/pr-investigator/
│   ├── SKILL.md                    # Agent instructions
│   └── scripts/
│       ├── fetch_pr.sh            # GitHub API fetcher
│       ├── analyze_diff.py        # Risk analyzer
│       ├── trace_deps.py          # Dependency tracer
│       ├── run_validation.py      # Test runner
│       └── generate_report.py     # Report generator
├── demo/                          # Demo repo + sample data
├── install.sh                     # One-line installer
└── .github/workflows/             # GitHub Action for auto-review
```

### My Tech Stack

- **Hermes Agent**: The orchestrator — handles planning, tool use, and multi-step reasoning
- **Python 3 + stdlib**: Helper scripts for analysis (no external deps)
- **Bash**: GitHub API integration
- **GitHub Actions**: Auto-runs on every PR

## How I Used Hermes Agent

### Agentic Planning

The core of this project is the `SKILL.md` file — it's not just documentation, it's **agent instructions**. Hermes reads it and decides:

1. Which files to read first (based on risk score)
2. When to run validation (after understanding the changes)
3. How deep to trace dependencies (only for core files)

Hermes uses its built-in `todo` tool to track the 5 phases, so if validation fails in Phase 3, it can adapt the investigation plan.

### Heavy Tool Use

The skill orchestrates 6 tools across 28 toolsets:

- **`terminal`**: Runs analysis scripts, git commands, test suites
- **`read_file`**: Reads modified files and their dependencies
- **`web_search`**: Looks up security advisories for dependencies
- **`execute_code`**: Runs Python validation scripts in sandbox
- **`todo`**: Tracks investigation phases
- **`skill_manage`**: Learns from reviews and improves its own approach

### Progressive Disclosure

The skill uses Hermes' progressive disclosure pattern:

- **Level 0**: Skill name and description in the system prompt (~3k tokens)
- **Level 1**: Full SKILL.md loads only when the user invokes `/pr-investigator`
- **Level 2**: Individual reference files load on demand

This keeps token usage efficient — the agent doesn't carry PR review instructions into unrelated conversations.

### Memory & Learning

Because Hermes has persistent memory, the investigator learns over time:

- It remembers which projects use which test frameworks
- It learns the team's coding conventions from previous reviews
- It improves its risk scoring based on which findings actually mattered

## Why This Approach Wins

Most "AI code review" submissions will be static analyzers or diff summarizers. This is different because:

1. **It executes**: It runs tests, lint, and type checks — it doesn't just read
2. **It traces**: It finds upstream and downstream dependencies
3. **It adapts**: The investigation plan changes based on findings
4. **It reports**: Structured severity ratings, not vague suggestions
5. **It learns**: Hermes' memory system makes it better over time

## Try It Yourself

```bash
# Install Hermes Agent
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Install the skill
git clone https://github.com/yourusername/hermes-pr-investigator.git
cd hermes-pr-investigator
bash install.sh

# Set your GitHub token
echo 'GITHUB_TOKEN=ghp_xxx' >> ~/.hermes/.env

# Investigate a PR
hermes chat --toolsets skills -q "/pr-investigator https://github.com/owner/repo/pull/123"
```

Or set up the GitHub Action to automatically review every PR:

```yaml
name: Hermes PR Investigator
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  investigate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Hermes
        run: curl -fsSL ... | bash
      - name: Install Skill
        run: bash install.sh
      - name: Run Investigation
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: hermes chat --toolsets skills -q "/pr-investigator ${{ github.event.pull_request.html_url }}"
```

## What's Next

- **Focus modes**: `--focus security`, `--focus performance`, `--focus tests`
- **Custom rules**: Team-specific conventions via `.hermes/pr-rules.md`
- **Batch reviews**: Run across all open PRs nightly via Hermes cron
- **IDE integration**: ACP adapter for in-editor review requests

---

*Thanks for reading! If you found this interesting, give it a ❤️ and let me know what you'd want an agentic PR reviewer to catch.*
