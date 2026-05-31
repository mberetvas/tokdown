# Move stdout suppression to adapters + offline/download UX

## What to build

Each encoder adapter manages its own stdout/stderr noise instead of the CLI wrapping everything in `stdout_clean()`. The behaviour depends on cache state:

- **Cached model** → suppress stdout silently, fast path.
- **Uncached model** → allow progress bars on stderr, print "Downloading tokenizer…" so users don't stare at a frozen terminal.
- **Offline + uncached** → raise a clear error: "Model not cached and network unavailable."

End-to-end: `huggingface_encoder.py` detects cache state and behaves accordingly → `tiktoken_encoder.py` does the same for its encoding files → `stdout_clean.py` deleted → `cli.py` no longer wraps execution in the context manager → tests verify stdout not polluted (cached) and offline error message correct.

## Acceptance criteria

- [ ] `huggingface_encoder.py`: cached → suppress stdout; uncached → stderr progress + "Downloading tokenizer…"; offline + uncached → clear `RuntimeError`
- [ ] `tiktoken_encoder.py`: same cache/offline pattern for tiktoken encoding files
- [ ] `stdout_clean.py` deleted from `interface/_internal/`
- [ ] `cli.py` no longer uses `stdout_clean()` wrapper
- [ ] `interface/_internal/__init__.py` updated (no re-export of deleted module)
- [ ] Tests: stdout not polluted when model is cached
- [ ] Tests: offline + uncached produces a user-friendly error message
- [ ] `uv run pytest` green, `uv run ruff check src/ tests/` clean
- [ ] Architecture boundary tests still pass

## Blocked by

- [001 — Add `hard_split` to `ChunkSizer` protocol + fix round-trip bug](001-hard-split-protocol-and-round-trip-fix.md)
