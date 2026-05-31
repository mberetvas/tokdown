# YAML frontmatter preservation

## What to build

Detect YAML frontmatter (`---\n...\n---` at file start) and ensure it stays intact in the first chunk only. Subsequent chunks do not receive a copy.

End-to-end: `markdown_regions.py` gains `RegionKind.FRONTMATTER` detection → splitter glues frontmatter to the first chunk as an unsplittable block (counts against the limit) → edge cases handled (frontmatter exceeds limit: warn + include anyway; unclosed frontmatter: treat as prose) → tests verify first-chunk-only behaviour.

## Acceptance criteria

- [ ] `RegionKind.FRONTMATTER` added to `markdown_regions.py`
- [ ] `iter_regions()` detects `---\n...\n---` at file start and yields a `FRONTMATTER` region
- [ ] Splitter glues frontmatter to the first chunk; it is unsplittable and counts against the chunk limit
- [ ] If frontmatter alone exceeds the limit: warn via logger, include anyway (don't crash)
- [ ] Unclosed frontmatter (no closing `---`) is treated as prose
- [ ] Part 2+ never contain frontmatter
- [ ] Tests: file with frontmatter → part 1 has it, part 2+ don't
- [ ] Tests: frontmatter exceeding limit → warning logged, included in part 1
- [ ] Tests: unclosed frontmatter → treated as regular prose
- [ ] `uv run pytest` green, `uv run ruff check src/ tests/` clean
- [ ] Architecture boundary tests still pass

## Blocked by

- [004 — Deepen `DocumentSplittingDomain` facade with validation](004-deepen-facade-validation.md)
