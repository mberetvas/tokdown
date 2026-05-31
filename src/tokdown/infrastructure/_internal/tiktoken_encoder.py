import sys
from dataclasses import dataclass
from typing import Any

from .suppress_stdout import suppress_stdout


@dataclass(frozen=True)
class TiktokenEncoder:
    _encoding: Any

    def encode(self, text: str) -> list[int]:
        return self._encoding.encode(text)

    def decode(self, token_ids: list[int]) -> str:
        return self._encoding.decode(token_ids)


def _is_cached(encoding_name: str) -> bool:
    """Check whether a tiktoken encoding is already loaded or file-cached."""
    try:
        import tiktoken
    except ImportError:
        return False

    if encoding_name in tiktoken.registry.ENCODINGS:
        return True

    # Probe file cache by temporarily blocking downloads
    import tiktoken.load as _load

    original_read_file = _load.read_file

    class _NotCached(Exception):
        pass

    def _block_download(blobpath: str) -> bytes:
        raise _NotCached

    _load.read_file = _block_download
    try:
        tiktoken.get_encoding(encoding_name)
        return True
    except _NotCached:
        return False
    except Exception:
        return False
    finally:
        _load.read_file = original_read_file
        # Clear any partially-registered encoding from the in-memory cache
        tiktoken.registry.ENCODINGS.pop(encoding_name, None)


def create_encoder(model_id: str) -> TiktokenEncoder:
    try:
        import tiktoken
    except ImportError:
        msg = (
            "tiktoken is required for OpenAI token counting."
            " Install it: uv add tiktoken"
        )
        raise ImportError(msg) from None

    if _is_cached(model_id):
        with suppress_stdout():
            encoding = tiktoken.get_encoding(model_id)
        return TiktokenEncoder(encoding)

    # Not cached — download with progress on stderr
    # Not cached — download with progress on stderr
    print("Downloading tokenizer\u2026", file=sys.stderr)
    try:
        with suppress_stdout():
            encoding = tiktoken.get_encoding(model_id)
    except (KeyError, ValueError):
        raise
    except Exception as exc:
        msg = (
            f"Encoding '{model_id}' is not cached"
            " and network is unavailable."
            f" Original error: {exc}"
        )
        raise RuntimeError(msg) from exc

    return TiktokenEncoder(encoding)

    return TiktokenEncoder(encoding)
