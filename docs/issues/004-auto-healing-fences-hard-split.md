---
id: 004
title: Auto-healing fences on forced hard-split
type: AFK
labels: [needs-triage]
status: open
blocked_by: [003]
---

# Auto-healing fences on forced hard-split

## What to build

When a single fenced block is larger than the limit and `MarkdownChunkingService`
must hard-split inside the fence, keep both chunks as valid markdown so LLM
context is not poisoned.

- End of chunk A: append `\n{indent}{marker * marker_len}\n` (closing fence).
- Start of chunk B: prepend `\n{indent}{marker * marker_len}{info_string}\n`
  (reopen with the same marker char/length and original info string).
- Log a `code_block_hard_split` event at WARN level with `fence_language` /
  `marker` metadata (event emission can be a no-op port until slice #008 wires
  real logging).

## Acceptance criteria

- [ ] `tests/domain/_internal/test_chunking_service.py`: an oversized
      ```` ```python ```` block splits into two chunks; chunk 1 ends with a
      closing fence; chunk 2 starts with a reopening fence carrying the same info
      string; inner code is never orphaned outside a fence.
- [ ] Healing preserves the original indent, marker character, and marker length.
- [ ] A `code_block_hard_split` WARN event is emitted with language/marker
      metadata.
- [ ] Slices #002 and #003 tests stay green; `ruff check` + `pytest -m "not
      slow"` pass.

## Blocked by

- #003 (markdown-aware code-fence preservation)
