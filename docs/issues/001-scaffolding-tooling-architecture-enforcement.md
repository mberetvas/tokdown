---
id: 001
title: Project scaffolding, tooling & architecture enforcement
type: AFK
labels: [needs-triage]
status: open
blocked_by: []
---

# Project scaffolding, tooling & architecture enforcement

## What to build

Lay the foundation that every later slice depends on: dependencies, package
skeleton, test runner, and the mechanically-enforced `_internal` import ban.

- Dependencies: keep `tiktoken`; `uv add transformers sentencepiece`;
  `uv add --dev pytest ruff`.
- Ruff config in `pyproject.toml`: `select` includes `E`, `F`, `I`, `TID252`,
  `TID`; `flake8-tidy-imports.banned-api` bans
  `tokdown.{interface,application,infrastructure,domain}._internal` outside
  their owning package; `per-file-ignores` grant `TID251` to each layer's
  `api.py` and to `tests/domain/_internal/**`.
- Pytest config in `pyproject.toml`: `[tool.pytest.ini_options]` with
  `testpaths = ["tests"]` and `pythonpath = ["src"]`; register `slow` marker.
- Package skeleton matching the plan's layout: empty `api.py` (and
  `application/ports.py`, `domain/logging/api.py`) plus `_internal/` packages
  for `interface`, `application`, `infrastructure`, `domain`.

This is foundational rather than a true vertical slice, but it is a hard
prerequisite for the ruff + TDD discipline the plan mandates.

## Acceptance criteria

- [ ] `uv sync` installs `tiktoken`, `transformers`, `sentencepiece`, and dev
      deps `pytest`, `ruff`.
- [ ] `uv run ruff check src tests` passes on the empty skeleton.
- [ ] A deliberate cross-layer `_internal` import (e.g. importing
      `tokdown.domain._internal.*` from `application/`) makes `ruff check` fail.
- [ ] `tokdown.{interface,application,infrastructure,domain}` packages exist with
      an `api.py` facade and an `_internal/` package each; `application/ports.py`
      and `domain/logging/api.py` exist.
- [ ] `uv run pytest` runs (zero tests is acceptable) and the `slow` marker is
      registered without warnings.

## Blocked by

- None - can start immediately.
