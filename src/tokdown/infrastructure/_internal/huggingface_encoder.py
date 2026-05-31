from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HuggingFaceEncoder:
    _tokenizer: Any

    def encode(self, text: str) -> list[int]:
        return self._tokenizer.encode(text, add_special_tokens=False)

    def decode(self, token_ids: list[int]) -> str:
        return self._tokenizer.decode(token_ids)


def create_encoder(model_id: str) -> HuggingFaceEncoder:
    import os

    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
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
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    return HuggingFaceEncoder(tokenizer)
