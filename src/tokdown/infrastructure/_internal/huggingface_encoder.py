from dataclasses import dataclass
from typing import Any

from tokdown.domain.api import TokenEncoder


@dataclass(frozen=True)
class HuggingFaceEncoder:
    _tokenizer: Any

    def encode(self, text: str) -> list[int]:
        return self._tokenizer.encode(text, add_special_tokens=False)

    def decode(self, token_ids: list[int]) -> str:
        return self._tokenizer.decode(token_ids)


class HuggingFaceEncoderFactory:
    def create(self, model_id: str) -> TokenEncoder:
        import os

        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
        os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")

        from transformers import AutoTokenizer
        from transformers.utils import logging as hf_logging

        hf_logging.set_verbosity_error()
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        return HuggingFaceEncoder(tokenizer)
