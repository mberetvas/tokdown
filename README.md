# tokdown

Split markdown documents into size-bounded parts for LLM context windows. Tokdown preserves fenced code blocks where possible and auto-heals fences when a block must be hard-split.

Chunk limits can be expressed in **Google tokens** (Hugging Face tokenizer), **OpenAI tokens** (tiktoken), or **words**.

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) for dependencies and commands

## Install

```bash
uv sync
```

## Usage

```text
tokdown [options] <input_file> <limit> [output_dir]
```

| Argument | Description |
| -------- | ----------- |
| `input_file` | Source `.md` file to split |
| `limit` | Maximum size per part (tokens or words, depending on mode) |
| `output_dir` | Optional output directory (defaults to the source file’s parent) |

Parts are written as `{stem}_part{n}.md` (for example `notes_part1.md`).

### Google tokens (default)

Uses a Hugging Face tokenizer. Default model: `google/gemma-2-2b`.

```bash
uv run tokdown document.md 4000
uv run tokdown --provider google -m google/gemma-2-2b document.md 4000 ./parts
```

### OpenAI tokens

Uses tiktoken. Default encoding: `cl100k_base`.

```bash
uv run tokdown --provider openai document.md 100
uv run tokdown --provider openai -m cl100k_base document.md 100 ./parts
```

### Words

Does not load tiktoken or transformers.

```bash
uv run tokdown --words document.md 500
```

### Overwrite policy

By default, tokdown refuses to overwrite existing part files. Use `--force` to replace them.

```bash
uv run tokdown --words document.md 500 ./parts
uv run tokdown --words --force document.md 500 ./parts
```

### Logging

Structured logs are written to **stderr**. User-facing success messages go to **stdout** unless `--quiet` is set.

| Flag | Description |
| ---- | ----------- |
| `--log-level` | Minimum level: `debug`, `info`, `warn`, `error` (default: `info`) |
| `--log-format` | `text` (human-readable) or `json` (one JSON object per line) |
| `--quiet` | Suppress success output on stdout |

```bash
uv run tokdown --log-format json --log-level warn document.md 4000
uv run tokdown --words --quiet document.md 500
```

Example JSON log fields: `level`, `event`, `correlation_id`, `token_provider`, plus event-specific context in snake_case (no document body or other PII).

## Providers and logging notes

**Token counts differ by provider.** The same markdown can produce different part counts under Google vs OpenAI vs words. Use the `--provider` (and `-m`) that matches the model you will send the chunks to.

| Mode | Library loaded | When |
| ---- | -------------- | ---- |
| `--provider google` | `transformers` (+ `sentencepiece` for some models) | Lazy-loaded on first Google split |
| `--provider openai` | `tiktoken` | Lazy-loaded on first OpenAI split |
| `--words` | Neither | Never |

**Google / Hugging Face**

- First run may download the tokenizer from the Hugging Face Hub (network latency).
- `google/gemma-2-2b` is a gated model: accept the license on the Hub and authenticate (`huggingface-cli login`) if downloads fail.
- Encodes use `add_special_tokens=False` so BOS/special tokens do not count toward limits.

**OpenAI / tiktoken**

- Offline after the encoding is available; no model weights are downloaded.

**Auto-healing fences**

Hard-splitting inside a code fence adds closing/reopening fence lines. That slightly increases token/word counts but keeps each part valid markdown for LLMs.

## Architecture

Tokdown uses a **facade per layer**: each package exposes a single public `api.py`. Implementation details live in `_internal/` and must not be imported across layer boundaries.

**Composition modules** (`<layer>/_internal/composition.py`) wire adapters and use cases inside each layer. Non-domain facades re-export from composition with a single `# noqa: TID251` import line in `api.py`. The domain facade (`domain/api.py`) keeps a file-level TID251 ignore because it is the only public surface for domain internals.

```text
src/tokdown/
  interface/api.py                    → main() (one noqa re-export from composition)
  interface/_internal/composition.py  → run_cli()
  application/api.py                  → SplitDocumentApplication, DTOs
  application/_internal/composition.py
  application/ports.py                → DocumentGateway
  domain/api.py                       → DocumentSplittingDomain (pure string splitting)
  domain/logging/api.py               → StructuredLogger port, LogEvent constants
  infrastructure/api.py             → create_infrastructure() (one noqa re-export)
  infrastructure/_internal/composition.py
```

**Allowed imports**

| From | May import |
| ---- | ---------- |
| `interface` | `application.api`, `domain.api`, `infrastructure.api` |
| `application` | `domain.api`, `application.ports` |
| `infrastructure` | `application.ports`, `domain.api`, `domain.logging.api` |
| `domain` (other packages) | `domain.api` only |
| `<layer>/_internal/**` | Same layer’s `_internal` only |
| Non-domain `api.py` | Its own `_internal.composition` only (one `# noqa: TID251` line) |
| `domain/api.py` | `domain._internal` (file-level TID251 ignore) |
| `tests/domain/_internal/` | `domain._internal` (chunking edge cases only) |

**Enforcement (merge blocker)**

Cross-layer `_internal` imports are not allowed. Ruff (`TID252`, `flake8-tidy-imports` `banned-api`) and `tests/architecture/test_internal_import_boundaries.py` (AST walk of `src/tokdown`) enforce this. CI and local checks must pass:

```bash
uv run ruff check src tests
uv run pytest tests/architecture -q
```

## Development

Install dependencies and dev tools:

```bash
uv sync
```

**Lint**

```bash
uv run ruff check src tests
```

**Test (fast, default for day-to-day work)**

```bash
uv run pytest -m "not slow"
```

Slow tests cover Hugging Face tokenizers (download/cache). Run the full suite before release when the HF cache is warmed and Hub access is configured:

```bash
uv run pytest
```

**Workflow**

Development is test-driven: add or extend tests under `tests/`, implement behind the layer `api.py` facades, and keep `ruff check` green. Prefer facade tests; use `tests/domain/_internal/` only for markdown fence edge cases.

**Layout**

```text
tests/
  architecture/        # import-boundary AST guard
  domain/              # domain.api facade
  domain/_internal/    # chunking / fence tests
  domain/logging/      # logging port contract
  application/         # use case + ports
  infrastructure/      # gateway, encoders, JSON logger
  interface/           # CLI end-to-end
  fakes/               # in-memory gateways and loggers
```

## License

See repository license terms (if applicable).
