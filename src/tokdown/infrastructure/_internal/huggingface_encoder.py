import os
import sys
from dataclasses import dataclass
from typing import Any

from .suppress_stdout import suppress_stdout


@dataclass(frozen=True)
class HuggingFaceEncoder:
    _tokenizer: Any

    def encode(self, text: str) -> list[int]:
        return self._tokenizer.encode(text, add_special_tokens=False)

    def decode(self, token_ids: list[int]) -> str:
        return self._tokenizer.decode(token_ids)


def create_encoder(model_id: str) -> HuggingFaceEncoder:
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

    try:
        from transformers import AutoTokenizer
        from transformers.utils import logging as hf_logging
    except ImportError:
        msg = (
            "transformers is required for Hugging Face token"
            " counting. Install it: uv add transformers"
        )
        raise ImportError(msg) from None

    hf_logging.set_verbosity_error()

    # Cached path: suppress all output
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    try:
        with suppress_stdout():
            tokenizer = AutoTokenizer.from_pretrained(
                model_id, local_files_only=True
            )
        return HuggingFaceEncoder(tokenizer)
    except OSError:
        pass  # Not cached locally, fall through to download

    # Uncached: allow stderr progress, print download notice
    os.environ.pop("HF_HUB_DISABLE_PROGRESS_BARS", None)
    print("Downloading tokenizer\u2026", file=sys.stderr)
    try:
        with suppress_stdout():
            tokenizer = AutoTokenizer.from_pretrained(model_id)
    except OSError as exc:
        msg = (
            f"Model '{model_id}' is not cached and network is unavailable."
            f" Original error: {exc}"
        )
        raise RuntimeError(msg) from exc

    return HuggingFaceEncoder(tokenizer)
    return HuggingFaceEncoder(tokenizer)
