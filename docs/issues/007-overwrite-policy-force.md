---
id: 007
title: Overwrite policy / --force
type: AFK
labels: [needs-triage]
status: open
blocked_by: [002]
---

# Overwrite policy / --force

## What to build

Refuse to clobber existing part files by default; allow opt-in overwrite, and
fail gracefully with a logged error.

- Application: `PartFileExistsError` in `application/ports.py` (re-exported from
  `application/api.py`); `SplitDocumentRequest.force: bool = False`.
- Gateway: `save_part(..., *, force: bool)` raises `PartFileExistsError` when
  `{stem}_part{n}.md` exists and `force=False`.
- Use case: on `PartFileExistsError`, log `output_file_exists` (ERROR) and fail
  gracefully so the CLI exits 1.
- Interface: `--force` flag mapped to `SplitDocumentRequest.force`.

## Acceptance criteria

- [ ] Application test: running against existing part files without `--force`
      raises `PartFileExistsError`; with `--force` the files are overwritten.
- [ ] CLI exits 1 (not a traceback) when a part file exists and `--force` is
      absent, and emits an `output_file_exists` ERROR event.
- [ ] `uv run tokdown ... --force` overwrites existing parts and exits 0.
- [ ] `ruff check` + `pytest -m "not slow"` pass.

## Blocked by

- #002 (end-to-end --words split via CLI)
