import contextlib
import io
import sys
from collections.abc import Generator


@contextlib.contextmanager
def suppress_stdout() -> Generator[None]:
    """Redirect stdout so third-party libs cannot pollute it."""
    original = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = original
