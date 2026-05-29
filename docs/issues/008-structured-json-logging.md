---
id: 008
title: Structured JSON logging
type: AFK
labels: [needs-triage]
status: open
blocked_by: [002]
---

# Structured JSON logging

## What to build

Cross-cutting structured logging: a domain-level port with semantic events and an
infrastructure JSON implementation, surfaced through CLI flags.

- Domain subdomain `domain/logging/api.py`: `StructuredLogger` ABC
  (`event(level, event_name, **context)`), `LogLevel` enum, `LogEvent` semantic
  constants. No JSON, stderr, or sanitization here.
- Infrastructure `_internal/logging/`: `JsonStructuredLogger`, plus `sanitizer`
  and `schema` modules. Fields include `correlation_id`, `token_provider`,
  `event`; snake_case keys; no PII.
- Wire the logger into the `Infrastructure` bundle and inject the port into the
  application, replacing any no-op logger used by earlier slices.
- Interface: `--log-level`, `--log-format` (json|text), `--quiet` (suppresses
  stdout) mapped into `InfraSettings`.

## Acceptance criteria

- [ ] `tests/domain/logging/test_logging_api.py` covers `LogEvent` constants and
      the fake-logger contract.
- [ ] `tests/infrastructure/test_json_logger.py` asserts the JSON line schema
      includes `correlation_id` and snake_case keys with no PII.
- [ ] `--log-format json` emits structured JSON lines; `--log-format text` emits
      human-readable lines; `--quiet` suppresses stdout.
- [ ] Earlier events (`code_block_hard_split`, `output_file_exists`) flow through
      the real logger.
- [ ] `ruff check` + `pytest -m "not slow"` pass.

## Blocked by

- #002 (end-to-end --words split via CLI)
