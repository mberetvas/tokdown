import pytest

from tokdown.application.dtos import SizerConfig
from tokdown.domain.api import ChunkUnit
from tokdown.infrastructure.api import create_infrastructure


def test_tiktoken_round_trip_and_known_token_count() -> None:
    factory = create_infrastructure().chunk_sizer_factory
    sizer = factory.create_for(
        SizerConfig(
            unit=ChunkUnit.TOKENS,
            token_provider="openai",
            model_id="cl100k_base",
        ),
    )
    encoder = sizer.encoder

    text = "one two three"
    token_ids = encoder.encode(text)

    assert sizer.measure(text) == 3
    assert len(token_ids) == 3
    assert encoder.decode(token_ids) == text
    assert len(encoder.encode(encoder.decode(token_ids))) == 3


def _skip_if_hf_model_unavailable(exc: BaseException) -> None:
    message = str(exc).lower()
    if "gated repo" in message or "restricted" in message:
        pytest.skip("google/gemma-2-2b requires Hugging Face access and cache")


@pytest.mark.slow
def test_huggingface_encode_omits_special_tokens() -> None:
    factory = create_infrastructure().chunk_sizer_factory
    try:
        sizer = factory.create_for(
            SizerConfig(
                unit=ChunkUnit.TOKENS,
                token_provider="google",
                model_id="google/gemma-2-2b",
            ),
        )
    except OSError as exc:
        _skip_if_hf_model_unavailable(exc)
        raise
    encoder = sizer.encoder
    tokenizer = encoder._tokenizer
    text = "hello world"

    with_special = len(tokenizer.encode(text, add_special_tokens=True))
    without_special = len(encoder.encode(text))

    assert without_special < with_special
