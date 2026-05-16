---
name: pr-investigator
description: Autonomous Pull Request investigator that plans, executes, and reports comprehensive code reviews using multi-step agentic reasoning
version: 1.0.0
author: Hermes PR Investigator Team
license: MIT
metadata:
  hermes:
    tags: [code-review, git, github, automation, devops]
    category: devops
    requires_toolsets: [terminal, file, web]
    config:
      - key: pr_investigator.default_repo
        description: Default repository to investigate when no full URL is provided
        default: ""
        prompt: Default GitHub repository (owner/repo format)
      - key: pr_investigator.max_files_to_read
        description: Maximum number of modified files to read in full per investigation
        default: "20"
        prompt: Max files to read per PR investigation
      - key: pr_investigator.test_timeout
        description: Timeout in seconds for test execution
        default: "300"
        prompt: Test execution timeout (seconds)
      - key: pr_investigator.report_format
        description: Output report format
        default: markdown
        prompt: Report format (markdown or json)
required_environment_variables:
  - name: GITHUB_TOKEN
    prompt: GitHub Personal Access Token
    help: Create one at https://github.com/settings/tokens with 'repo' scope
    required_for: fetching PR data from GitHub API
---

# PR Investigator

An autonomous pull request investigation skill for Hermes Agent. Given a PR URL or local branch, this skill plans and executes a deep multi-step code review that goes beyond surface-level diff summaries.

## When to Use

Load this skill when the user wants to:
- Review a pull request thoroughly before merging
- Understand the impact and risks of a code change
- Check for missing tests, unhandled edge cases, or breaking changes
- Get an autonomous agentic review that reads files, runs tests, and validates assumptions

## Quick Reference

```
/pr-investigator https://github.com/owner/repo/pull/123
/pr-investigator local --branch feature/auth-refactor
/pr-investigator https://github.com/owner/repo/pull/456 --focus security
/pr-investigator https://github.com/owner/repo/pull/789 --focus tests
```

## Investigation Strategy

The PR Investigator follows a strict multi-phase workflow:

### Phase 1: Discovery & Planning
1. Fetch PR metadata (title, description, author, branch info)
2. Fetch the diff (files changed, lines added/removed)
3. Create an investigation plan using the `todo` tool
4. Identify high-risk files (large changes, core modules, public APIs)

### Phase 2: Deep File Analysis
1. Read each modified file in the PR
2. For each changed file, read upstream dependencies (files that import it)
3. Read downstream consumers (files it imports that changed)
4. Identify public API surface changes and breaking changes

### Phase 3: Validation
1. Check if tests exist for modified code
2. Run the test suite focused on changed areas
3. Run linting and type checking if configured
4. Search for TODOs, FIXMEs, or security anti-patterns

### Phase 4: Cross-Reference
1. Search the codebase for patterns that might be affected
2. Check for documentation that needs updating
3. Look for migration guides or changelog entries

### Phase 5: Report Generation
1. Compile findings into a structured report
2. Assign severity ratings (Critical, High, Medium, Low, Info)
3. Suggest specific fixes with file references
4. Generate a markdown report using the template

## Procedure

### GitHub PR Investigation

When given a GitHub PR URL:

1. **Fetch PR data** using the helper script:
   ```bash
   bash ${HERMES_SKILL_DIR}/scripts/fetch_pr.sh <pr_url> <github_token>
   ```
   This creates `.hermes/pr-data/pr_<number>.json` with metadata and `.hermes/pr-data/diff_<number>.patch`.

2. **Parse and plan**:
   ```bash
   python3 ${HERMES_SKILL_DIR}/scripts/analyze_diff.py --plan .hermes/pr-data/diff_<number>.patch
   ```
   This outputs a JSON investigation plan. Load it and create todos.

3. **Read modified files**: Use `read_file` to read each file in the diff. Focus on:
   - Files with >100 lines changed
   - Files in `src/`, `lib/`, or core directories
   - Files touching authentication, authorization, or data handling
   - Any file removing functionality

4. **Trace dependencies**: For each core changed file:
   ```bash
   python3 ${HERMES_SKILL_DIR}/scripts/trace_deps.py <file_path> <repo_root>
   ```

5. **Run validation**:
   ```bash
   cd <repo_root> && python3 ${HERMES_SKILL_DIR}/scripts/run_validation.py --files <changed_files>
   ```

6. **Generate report**:
   ```bash
   python3 ${HERMES_SKILL_DIR}/scripts/generate_report.py --pr-data .hermes/pr-data/pr_<number>.json --findings .hermes/pr-data/findings.json
   ```

### Local Branch Investigation

When given a local branch:

1. **Generate diff**:
   ```bash
   git diff main...<branch> > .hermes/pr-data/local_diff.patch
   git log --oneline main..<branch> > .hermes/pr-data/commits.txt
   ```

2. Follow phases 2-5 above using the local diff.

## Focus Modes

The user can request a specific focus. Adjust the investigation:

- `--focus security`: Prioritize auth code, input validation, SQL queries, secrets detection
- `--focus tests`: Prioritize test coverage, missing tests, flaky test detection
- `--focus performance`: Prioritize algorithmic complexity, DB queries, N+1 patterns
- `--focus architecture`: Prioritize coupling, cohesion, SOLID violations

## Pitfalls

- **Large PRs**: If >50 files changed, sample the most critical files and note the limitation
- **Binary files**: Skip binary files; note their presence
- **Generated code**: Ask whether files are generated; skip generated code unless relevant
- **No tests**: If the repo has no test infrastructure, skip Phase 3 validation and note it
- **API rate limits**: GitHub API has rate limits. If hit, fall back to local git operations if the repo is cloned

## Verification

A successful investigation produces:
1. A `.hermes/pr-data/` directory with raw data
2. A structured markdown report at `.hermes/reports/pr_<number>_report.md`
3. A summary of findings with severity ratings
4. Specific actionable recommendations

## Report Template

Reports follow this structure:

```markdown
# PR Investigation Report: <Title>

## Executive Summary
- PR: <URL>
- Author: <Author>
- Files Changed: <N>
- Lines Added/Removed: <+N/-M>
- Overall Risk: <Low|Medium|High|Critical>

## Findings

### Critical
1. **[C-1]** <Description> - `file:line`
   - **Impact**: <What could go wrong>
   - **Fix**: <Specific suggestion>

### High
...

### Medium
...

### Low / Info
...

## Validation Results
- Tests: <Pass|Fail|Skipped> (<N> tests run)
- Lint: <Pass|Fail|N/A>
- Coverage Impact: <+/-N%>

## Recommendations
1. <Actionable item>
2. <Actionable item>

## Investigation Log
- Phase 1: Discovery (completed)
- Phase 2: Deep Analysis (N files read)
- Phase 3: Validation (tests run: Y)
- Phase 4: Cross-Reference (N patterns found)
- Phase 5: Report Generation (completed)
```
