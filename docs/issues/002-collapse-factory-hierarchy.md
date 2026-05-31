# Collapse factory hierarchy + `ImportError` guards

## What to build

Kill the factory-of-factories pattern. Delete `token_encoder_factory.py` (the `TokenEncoderFactory` abstract base and `CompositeTokenEncoderFactory` composite) and absorb the provider-routing logic directly into `sizing_factory.py` as a single decision tree.

Simplify encoder files: `TiktokenEncoderFactory` and `HuggingFaceEncoderFactory` classes become plain `create_encoder(model_id)` functions. Add `try/except ImportError` guards in each encoder module with user-friendly messages (e.g., "Install tiktoken: uv add tiktoken").

End-to-end: `sizing_factory.py` routes by provider name → calls `create_encoder()` in the appropriate encoder module → encoder module guards its own import → `TokenChunkSizer` built with the result. One module, one decision tree, clear errors if a dep is missing.

## Acceptance criteria

- [ ] `token_encoder_factory.py` deleted
- [ ] `sizing_factory.py` contains all provider-routing logic (no abstract base, no composite)
- [ ] `tiktoken_encoder.py` exports a `create_encoder(model_id) -> TiktokenEncoder` function (factory class removed or replaced)
- [ ] `huggingface_encoder.py` exports a `create_encoder(model_id) -> HuggingFaceEncoder` function (factory class removed or replaced)
- [ ] Each encoder module wraps its third-party import in `try/except ImportError` with a clear message
- [ ] All references to deleted types updated (composition modules, tests, `__init__.py` re-exports)
- [ ] `uv run pytest` green, `uv run ruff check src/ tests/` clean
- [ ] Architecture boundary tests still pass

## Blocked by

- [001 — Add `hard_split` to `ChunkSizer` protocol + fix round-trip bug](001-hard-split-protocol-and-round-trip-fix.md)
