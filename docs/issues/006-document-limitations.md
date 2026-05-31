# Document accepted limitations in README

## What to build

Add a "Limitations" section to `README.md` covering two accepted design trade-offs:

1. **Whitespace normalization** — `\n\n\n` becomes `\n\n`. By design: markdown renderers treat them identically.
2. **File size / OOM** — The entire file is loaded into memory. tokdown is designed for LLM context prep (typical files < 1 MB), not multi-GB log processing.

## Acceptance criteria

- [ ] `README.md` contains a "Limitations" section
- [ ] Whitespace normalization documented as intentional (with rationale)
- [ ] File-size scope documented (LLM context prep, not large-file processing)
- [ ] No code changes

## Blocked by

- [005 — YAML frontmatter preservation](005-yaml-frontmatter-preservation.md)
