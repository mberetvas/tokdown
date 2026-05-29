---
id: 006
title: Google token provider (HF) with lazy imports
type: AFK
labels: [needs-triage]
status: open
blocked_by: [005]
---

# Google token provider (HF) with lazy imports

## What to build

Add the Google provider via a HuggingFace tokenizer, with strict lazy loading so
`--words` and `--provider openai` never pay the cost, and prove it with an
automated regression test.

- Infrastructure `_internal`: `HuggingFaceEncoder` with
  `from transformers import AutoTokenizer` inside `create()` only. Every encode
  used for measuring or hard-splitting uses
  `tokenizer.encode(text, add_special_tokens=False)` so `<bos>`/special tokens
  never count toward limits.
- Silence upstream HF noise inside the lazy block before `from_pretrained`:
  `os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")` and
  `transformers.utils.logging.set_verbosity_error()`.
- Interface: default mode is `--provider google -m google/gemma-2-2b`.
- HF-dependent tests marked `@pytest.mark.slow`.

## Acceptance criteria

- [ ] An infrastructure test asserts a known string's token count decreases with
      `add_special_tokens=False` versus `True` (or matches a fixed expected
      count). Marked `@pytest.mark.slow`.
- [ ] `tests/interface/test_main_cli.py` runs `main()` with `--words` in a
      subprocess (fresh interpreter) and asserts
      `{"transformers": False, "tiktoken": False}` in `sys.modules`.
- [ ] No top-level `transformers` import in `infrastructure/api.py`,
      `composition.py`, or the composite factory.
- [ ] `uv run tokdown --provider google <file> <limit>` splits by Google token
      count and exits 0.
- [ ] `ruff check` + `pytest -m "not slow"` pass; full `uv run pytest` passes
      when the HF cache is warmed.

## Blocked by

- #005 (OpenAI token provider — establishes the factory routing this extends)
