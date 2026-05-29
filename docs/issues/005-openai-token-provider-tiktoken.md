---
id: 005
title: OpenAI token provider (tiktoken)
type: AFK
labels: [needs-triage]
status: open
blocked_by: [002]
---

# OpenAI token provider (tiktoken)

## What to build

Add token-based chunking for the OpenAI provider end-to-end, alongside the
existing word mode.

- Infrastructure `_internal`: `TiktokenEncoder` with `import tiktoken` inside the
  factory method only (no top-level import); `TokenChunkSizer` measuring chunk
  size in tokens; a `CompositeTokenEncoderFactory` / `ChunkSizerFactory` that
  routes by token provider and `model_id`. `TokenEncoderFactory` stays private to
  infrastructure `_internal` (not exported from `infrastructure/api.py`).
- Interface: `--provider openai -m cl100k_base` selects the tiktoken path and
  maps into `SplitDocumentRequest`.

## Acceptance criteria

- [ ] `tests/infrastructure/test_token_encoders.py` asserts a tiktoken round-trip
      / known token count (offline).
- [ ] `uv run tokdown --provider openai <file> <limit>` splits by OpenAI token
      count and exits 0.
- [ ] `tiktoken` is imported lazily inside the factory method, not at module top
      level in `infrastructure/api.py` or the composite factory.
- [ ] `infrastructure/api.py` does not export `TokenEncoderFactory`;
      `ChunkSizerFactory` is the only encoder entry point for the application.
- [ ] `ruff check` + `pytest -m "not slow"` pass.

## Blocked by

- #002 (end-to-end --words split via CLI)
