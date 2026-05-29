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

Tokdown has two subcommands: **count** (measure size) and **split** (write part files). Legacy invocations without a subcommand still work — they are treated as `split`.

```text
tokdown count [options] <input_file>
tokdown split [options] <input_file> <limit> [output_dir]
tokdown [options] <input_file> <limit> [output_dir]   # legacy → split
```

| Argument | Description |
| -------- | ----------- |
| `input_file` | Source `.md` file |
| `limit` | Maximum size per part (split only; tokens or words, depending on mode) |
| `output_dir` | Optional output directory for split (defaults to the source file’s parent) |

Parts are written as `{stem}_part{n}.md` (for example `notes_part1.md`).

### Count

Print a bare integer to **stdout** (one line, no labels) so shell scripts can compare sizes before splitting:

```bash
uv run tokdown count document.md
uv run tokdown count --words document.md
uv run tokdown count --provider openai document.md

if [ "$(uv run tokdown count --words doc.md)" -gt 4000 ]; then
  echo "Document too large for this step"
fi
```

| Stream | Success | Failure |
| ------ | ------- | ------- |
| stdout | Integer + newline only | **Empty** |
| stderr | Structured logs (if enabled) | Error message + logs |

Split keeps printing errors on stdout for backward compatibility with existing scripts.

When using the Google provider, tokdown reduces Hub/transformers noise on stderr (for example `HF_HUB_DISABLE_PROGRESS_BARS`, `TRANSFORMERS_NO_ADVISORY_WARNINGS`, `TOKENIZERS_PARALLELISM=false`, and lowered transformers log verbosity on lazy load).

### Google tokens (default)

Uses a Hugging Face tokenizer. Default model: `google/gemma-2-2b`.

```bash
uv run tokdown document.md 4000
uv run tokdown split document.md 4000
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

Structured logs are written to **stderr**. On **split**, success messages go to **stdout** unless `--quiet` is set (`count` has no success line on stdout).

| Flag | Description |
| ---- | ----------- |
| `--log-level` | Minimum level: `debug`, `info`, `warn`, `error` (default: `info`) |
| `--log-format` | `text` (human-readable) or `json` (one JSON object per line) |
| `--quiet` | **Split only** — suppress success output on stdout |

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

- Lazy-load sets `TOKENIZERS_PARALLELISM=false` and lowers transformers log verbosity; count mode also silences some Hub progress via `stdout_clean`.
- First run may download the tokenizer from the Hugging Face Hub (network latency).
- `google/gemma-2-2b` is a gated model: accept the license on the Hub and authenticate (`huggingface-cli login`) if downloads fail.
- Encodes use `add_special_tokens=False` so BOS/special tokens do not count toward limits.

**OpenAI / tiktoken**

- Offline after the encoding is available; no model weights are downloaded.

**Auto-healing fences**

Hard-splitting inside a code fence adds closing/reopening fence lines. That slightly increases token/word counts but keeps each part valid markdown for LLMs.

## Design

Tokdown is split into layers (interface, application, domain, infrastructure). Each layer exposes a single public `api.py`; implementation stays in that layer’s `_internal` and must not be imported across layers.

- **Splitting** prefers paragraph breaks in prose but treats fenced code blocks as atomic when possible.
- **Hard splits** inside a fence auto-close and re-open the fence so each part stays valid markdown for LLMs (small size overhead vs broken fences).
- **Sizing** is pluggable (words, OpenAI tiktoken, Google HF tokenizer); token counts differ by provider — match the mode to your target model.
- **Domain** is pure string math; filesystem and tokenizer adapters live in application/infrastructure ports.

Import boundaries, facade rules, and enforcement are documented in [docs/adr/001-layered-facades-and-imports.md](docs/adr/001-layered-facades-and-imports.md). Before merge:

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

Contributor tooling, package management (`uv`), and TDD policy: [AGENTS.md](AGENTS.md).

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

No license file is included in this repository yet.
