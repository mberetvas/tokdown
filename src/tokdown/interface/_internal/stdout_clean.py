import os
import sys
import warnings
from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def stdout_clean() -> Generator[None]:
    """Redirect stdout and warnings so only the final count reaches real stdout."""
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

    original_stdout = sys.stdout
    original_showwarning = warnings.showwarning

    def showwarning(
        message: Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: object | None = None,
        line: str | None = None,
    ) -> None:
        sys.stderr.write(
            warnings.formatwarning(message, category, filename, lineno, line),
        )

    warnings.showwarning = showwarning
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = original_stdout
        warnings.showwarning = original_showwarning
