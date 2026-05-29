---
id: 003
title: Markdown-aware code-fence preservation
type: AFK
labels: [needs-triage]
status: open
blocked_by: [002]
---

# Markdown-aware code-fence preservation

## What to build

Stop naive `\n\n` splitting from breaking fenced code blocks. Introduce a robust
line-based fence detector and route chunking through it.

- `domain/_internal/markdown_regions.py`: `FENCE_LINE =
  re.compile(r"^(\s*)(\`{3,}|~{3,})(.*)$")` and an `iter_regions(text)` iterator
  driven by the Closed/Open state machine — capture indent, marker char
  (`` ` `` or `~`), marker length (≥3), and info string; a closing fence must
  match marker char and length; trailing spaces allowed; malformed (open, no
  close) runs until EOF.
- `MarkdownChunkingService` consumes `iter_regions(text)` instead of raw
  `split("\n\n")`: prose regions may split on blank lines, fenced regions are
  atomic (no splitting on inner blank lines) until close or a forced hard-split.
- `DocumentSplittingDomain.split` delegates to the chunking service; the facade
  surface is unchanged.

Direct `_internal` tests are explicitly allowed here (markdown/chunking edge
cases) under `tests/domain/_internal/`.

## Acceptance criteria

- [ ] `tests/domain/_internal/test_markdown_regions.py` covers tildes `~~~`,
      trailing spaces on fence lines, info strings (e.g. `bash script.sh`), and
      4-backtick markers matched by `` `{3,} ``.
- [ ] A fenced block containing inner blank lines is NOT split on those blank
      lines (facade test: prose + fence under limit → single unchanged part).
- [ ] Malformed fence (opened, never closed) is treated as fenced until EOF.
- [ ] `MarkdownChunkingService` consumes `iter_regions`, not `split("\n\n")`.
- [ ] Existing slice #002 facade tests stay green; `ruff check` + `pytest -m
      "not slow"` pass.

## Blocked by

- #002 (end-to-end --words split via CLI)
