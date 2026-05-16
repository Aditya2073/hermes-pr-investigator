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

## Demo: Real-World Test on Hermes Agent Itself

I didn't just build this — I tested it on a real merged PR from the [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) repository:

**PR**: [#26957 — fix(acp): replay session history before responding to session/load](https://github.com/NousResearch/hermes-agent/pull/26957)

### What Hermes Did (Autonomously)

```bash
hermes chat --toolsets "skills,terminal,file,web" \
  -q "Investigate PR https://github.com/NousResearch/hermes-agent/pull/26957"
```

**Phase 1 — Discovery**: Fetched PR metadata via `gh pr view`, pulled diff via `gh pr diff`, checked CI status (`gh pr checks`)

**Phase 2 — Analysis**: Read `acp_adapter/server.py` and `tests/acp/test_server.py`. The PR removes `_schedule_history_replay` and switches from deferred `loop.call_soon` to awaited inline replay.

**Phase 3 — Validation**: Checked failing test logs via `gh run view --log-failed`. All 6 failures were pre-existing on main (registry manifest mismatch, PermissionError in CI runner, xAI dotenv issue) — not introduced by this PR.

**Phase 4 — Cross-Reference**: Searched codebase for orphan references to `_schedule_history_replay`. **Zero found** — clean removal.

**Phase 5 — Report**: Generated structured review with verdict.

### Findings from the Real PR

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 0 |
| Warnings | 0 |

**Suggestion**: The `try/except` blocks in `load_session` and `resume_session` are near-identical (differ only in log message string). Consider extracting a `_replay_session_history_guarded(self, state, operation: str)` helper for DRY.

**Verdict**: "This is a clean, well-researched fix. The bug was subtle — `loop.call_soon` makes the server look correct in isolated testing but breaks any client that inspects notification counts synchronously after `await loadSession()`. The fix aligns Hermes with every other ACP server and the spec's natural reading."

---

### Demo: Local Auth Branch

I also tested on a synthetic PR adding JWT auth to a Flask app:

```bash
hermes chat --toolsets skills -q \
  "Investigate the local branch feature/add-auth"
```

**What it found**:
- **High**: Hardcoded `JWT_SECRET` fallback (`"default-secret"`) in auth middleware
- **High**: `require_auth` decorator defined but **never applied** to any route
- **Medium**: 5 files changed, 0 test files modified
- **Medium**: Register endpoint lacks input validation or duplicate-user checks

See the full demo report in the repo: `demo/real-world-report-pr-26957.md`

## Code

**Repository**: [github.com/Aditya2073/hermes-pr-investigator](https://github.com/Aditya2073/hermes-pr-investigator)

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

Most "AI code review" submissions will be static analyzers or diff summarizers. I proved this is different by running it on a real PR and watching it:

1. **Execute**: It ran `gh pr checks`, `gh run view --log-failed`, and searched the actual codebase — not just reading the patch
2. **Trace**: It found zero orphan references to `_schedule_history_replay`, confirming clean removal
3. **Adapt**: When CI showed failures, it checked if they were pre-existing on main before flagging them
4. **Report**: Structured severity ratings (Critical/High/Medium/Low) with specific line references
5. **Reason**: It understood the *subtle* bug — `loop.call_soon` looking correct in isolation but breaking synchronous client inspection

The real PR test produced a 500-word technical review with a suggestion the human reviewers missed (DRY refactoring of near-identical try/except blocks).

## Try It Yourself

```bash
# Install Hermes Agent
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash

# Install the skill
git clone https://github.com/Aditya2073/hermes-pr-investigator.git
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
