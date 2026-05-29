---
id: 002
title: End-to-end --words split via CLI
type: AFK
labels: [needs-triage]
status: open
blocked_by: [001]
---

# End-to-end --words split via CLI

## What to build

The first tracer bullet: the thinnest path that cuts through every layer and is
demoable on its own. Running the CLI in word-count mode splits a markdown file
into part files on disk.

- Domain: `DocumentSplittingDomain.split(body, limit, sizer)` splitting prose on
  `\n\n` boundaries; `ChunkLimit`, `ChunkUnit`, `chunk_limit()`, the `ChunkSizer`
  / `TokenEncoder` protocols, and a `WordChunkSizer` (all behind `domain/api.py`,
  internals in `domain/_internal/`).
- Application: `SplitDocumentApplication.execute(SplitDocumentRequest)` →
  `SplitDocumentResult`; `DocumentGateway` port + `MarkdownDocument` /
  `DocumentPart` DTOs in `application/ports.py`, re-exported from
  `application/api.py`. Use-case flow: load → split → save parts.
- Infrastructure: `create_infrastructure(InfraSettings) -> Infrastructure`
  bundle exposing `document_gateway` (`FileSystemDocumentGateway`, UTF-8) and a
  `chunk_sizer_factory` that can produce a word sizer; constructor-injected into
  the application.
- Interface: `main(argv) -> int` parsing `tokdown --words <input> <limit>
  [output_dir]`, building settings, wiring infrastructure + application.

TDD order per the plan: domain facade test first (under limit → one chunk;
multi-part; word limit), then application with `FakeDocumentGateway`, then the
real gateway, then CLI e2e with `tmp_path`.

## Acceptance criteria

- [ ] `DocumentSplittingDomain.split` returns one chunk when body fits the limit
      and multiple chunks when it does not, measured by `WordChunkSizer`.
- [ ] `domain/api.__all__` exports the split surface only — no `DocumentGateway`,
      `TokenEncoderFactory`, `TokenProvider`, `MarkdownDocument`, or `DocumentPart`.
- [ ] `SplitDocumentApplication.execute` writes `{stem}_part{n}.md` via the
      gateway; verified against `FakeDocumentGateway` recording written parts.
- [ ] `FileSystemDocumentGateway` reads and writes UTF-8 files.
- [ ] `uv run tokdown --words <file> <limit>` exits 0 and writes the expected
      part files under `tmp_path`.
- [ ] `uv run ruff check src tests` and `uv run pytest -m "not slow"` pass.

## Blocked by

- #001 (scaffolding, tooling & architecture enforcement)
