# Add `hard_split` to `ChunkSizer` protocol + fix round-trip bug

## What to build

Extend the `ChunkSizer` protocol with a `hard_split(text: str, limit: int) -> list[str]` method so each sizer owns its own splitting strategy. Move the word-based splitting logic from `services.py::_hard_split` into `WordChunkSizer.hard_split`, and the token-based logic from `_hard_split_tokens` into `TokenChunkSizer.hard_split` — **without** the broken round-trip assertion.

End-to-end slice: protocol change → two concrete implementations → `MarkdownChunkingService` simplified (calls `sizer.hard_split()` instead of branching on type + `getattr` hack) → tests green.

### The round-trip bug

`_hard_split_tokens` slices token IDs by limit, decodes the chunk, then re-encodes to verify size. But `decode → encode` is asymmetric (subword normalization, prefix spaces), so the assertion `len(encoder.encode(chunk)) <= limit` randomly crashes on valid input. The token-ID slice is correct by construction — it is already `<= limit` tokens. Remove the assertion; trust the slice.

## Acceptance criteria

- [ ] `ChunkSizer` protocol declares `hard_split(self, text: str, limit: int) -> list[str]`
- [ ] `WordChunkSizer.hard_split` implements word-boundary splitting (logic moved from `services.py::_hard_split`)
- [ ] `TokenChunkSizer.hard_split` implements token-ID slicing without the round-trip assertion
- [ ] `MarkdownChunkingService._hard_split` delegates to `sizer.hard_split(text, limit.value)` — no type branching, no `getattr`
- [ ] `_hard_split_tokens` function deleted from `services.py`
- [ ] Existing tests pass; new unit tests cover each sizer's `hard_split` + a round-trip edge-case test
- [ ] `uv run pytest` green, `uv run ruff check src/ tests/` clean
- [ ] Architecture boundary tests still pass (`tests/architecture/`)

## Blocked by

None — can start immediately
