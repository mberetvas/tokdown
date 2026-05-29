---
id: 009
title: README & architecture docs
type: AFK
labels: [needs-triage]
status: open
blocked_by: [002, 005, 006, 008]
---

# README & architecture docs

## What to build

Document usage, architecture rules, and the development workflow once the major
behaviors exist.

- Usage for all three modes (`--provider google`, `--provider openai`, `--words`)
  including `--force` and logging flags.
- Architecture section: one `api.py` per layer; never import another layer's
  `_internal`; the ruff `TID252` + `banned-api` enforcement is a merge blocker.
- Development section: `uv sync`, `uv run ruff check src tests`,
  `uv run pytest -m "not slow"` (and full `uv run pytest` before release) with
  the TDD workflow.
- Logging and provider notes (per-provider token-count differences; HF first-run
  download latency).

## Acceptance criteria

- [ ] `README.md` documents all three chunking modes with example commands.
- [ ] Architecture and import rules are described, including the ruff
      enforcement.
- [ ] Development/verification commands are documented and accurate.
- [ ] Logging and provider trade-off notes are included.

## Blocked by

- #002 (end-to-end --words split via CLI)
- #005 (OpenAI token provider)
- #006 (Google token provider)
- #008 (structured JSON logging)
