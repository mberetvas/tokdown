import re

_SNAKE_CASE_KEY = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
_BLOCKED_CONTEXT_KEYS = frozenset(
    {
        "body",
        "content",
        "document_body",
        "email",
        "password",
        "source_text",
        "user_name",
        "username",
    }
)


def sanitize_context(context: dict[str, object]) -> dict[str, object]:
    """Drop PII-like keys and keys that are not snake_case."""
    sanitized: dict[str, object] = {}
    for key, value in context.items():
        if key in _BLOCKED_CONTEXT_KEYS:
            continue
        if not _SNAKE_CASE_KEY.match(key):
            continue
        sanitized[key] = value
    return sanitized
