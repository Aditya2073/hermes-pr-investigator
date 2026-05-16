# PR Investigation Report: fix(acp): replay session history before responding to session/load (#12285 follow-up)

> **Real-world test on NousResearch/hermes-agent PR #26957**

## Executive Summary

| Field | Value |
|-------|-------|
| **PR** | [#26957](https://github.com/NousResearch/hermes-agent/pull/26957) |
| **Author** | @kshitijk4poor |
| **State** | MERGED |
| **Files Changed** | 2 |
| **Additions** | +122 |
| **Deletions** | -31 |
| **Overall Risk** | **Low** |

## Summary

Switches `_replay_session_history` from deferred (`loop.call_soon` — fires after JSON-RPC response) to awaited inline (before the response). This makes `session/load` and `session/resume` ACP-spec-compliant: the full transcript is streamed back to the client within the request's lifetime, matching every other reference ACP server (Codex, Claude Code, OpenCode, Pi, agentao).

## What Changed

### `acp_adapter/server.py` (+47 / -22)
- Removes the `_schedule_history_replay` helper entirely (9 lines gone)
- Both `load_session` and `resume_session` now `await self._replay_session_history(state)` before constructing the response
- Each await wrapped in `try/except Exception` with `logger.warning(..., exc_info=True)` — preserves the contract that a bad message in history cannot turn a successful load into a JSON-RPC error

### `tests/acp/test_server.py` (+75 / -9)
- Removes `test_load_session_schedules_history_replay_after_response` (encoded the now-wrong post-response ordering)
- Adds `test_load_session_replays_history_before_returning_response` — asserts events == `["replay", "returned"]`
- Adds `test_resume_session_replays_history_before_returning_response` — same for the resume path
- Adds `test_load_session_survives_replay_helper_exception` — RuntimeError in replay helper still yields LoadSessionResponse
- Adds `test_resume_session_survives_replay_helper_exception` — same guarantee for resume

## Findings

### Critical: None

### Warnings: None

### Suggestions
- **acp_adapter/server.py:1020-1062** — The `try/except` blocks in `load_session` and `resume_session` are near-identical (differ only in the log message: `"session/load"` vs `"session/resume"`). Consider extracting into a `_replay_session_history_guarded(self, state, operation: str)` helper for DRY. Minor.

## Looks Good

- The root cause analysis in the commit message is thorough — cites Zed source code, the ACP spec, other reference servers, and the specific reproduction from the community reporter
- Zero orphan references to `_schedule_history_replay` — clean removal
- The `_fenced_text` change from the same original May 2 commit is correctly preserved as orthogonal
- Defensive `try/except Exception` wrapping is the right call — partial transcripts are better than total load failure
- Tests now assert temporal ordering (`"replay"` before `"returned"`) rather than relying on brittle `asyncio.sleep(0)` loops
- Regression tests explicitly cover the exception-propagation edge case that changed with the awaited replay
- CI: 23,372 passed, 6 failures — all 6 are pre-existing on main

## Security
No concerns. The broad `except Exception` is correctly scoped to a best-effort replay operation and does not mask auth or validation failures.

## Performance
No concerns. ACP SDK dispatches each RPC as an independent supervisor task, so awaiting replay doesn't block other requests on the same connection.

## Verdict

This is a clean, well-researched fix. The bug was subtle — `loop.call_soon` makes the server look correct in isolated testing but breaks any client that inspects notification counts synchronously after `await loadSession()`. The fix aligns Hermes with every other ACP server and the spec's natural reading. Tests are well-constructed and the regression coverage for exception propagation is thoughtful.

Already merged, so no action needed — but for future reference this is a textbook example of how ACP spec compliance bugs should be diagnosed and fixed.

---

*Investigated by Hermes PR Investigator on 2026-05-16*
*Target: https://github.com/NousResearch/hermes-agent/pull/26957*
