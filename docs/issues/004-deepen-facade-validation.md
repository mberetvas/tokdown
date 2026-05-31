# Deepen `DocumentSplittingDomain` facade with validation

## What to build

Move input validation from `MarkdownChunkingService.split()` up into the `DocumentSplittingDomain` facade. The facade becomes the single place that enforces `limit.value > 0` and handles the empty-body edge case (`return [""]`). After this, `MarkdownChunkingService.split()` assumes valid inputs — no defensive guards.

End-to-end: facade validates → delegates to service → service is pure algorithm → tests assert validation at facade level (not service level).

## Acceptance criteria

- [ ] `DocumentSplittingDomain.split()` raises `ValueError` when `limit.value <= 0`
- [ ] `DocumentSplittingDomain.split()` returns `[""]` for empty/whitespace-only body without calling the service
- [ ] `MarkdownChunkingService.split()` no longer contains input validation guards
- [ ] Existing tests pass; validation tests target the facade, not the service
- [ ] `uv run pytest` green, `uv run ruff check src/ tests/` clean
- [ ] Architecture boundary tests still pass

## Blocked by

- [002 — Collapse factory hierarchy + `ImportError` guards](002-collapse-factory-hierarchy.md)
- [003 — Move stdout suppression to adapters + offline/download UX](003-stdout-suppression-and-download-ux.md)
