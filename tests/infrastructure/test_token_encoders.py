import importlib
from pathlib import Path
from unittest.mock import patch

import pytest

from tokdown.application.dtos import SizerConfig
from tokdown.domain.api import ChunkUnit
from tokdown.infrastructure.api import create_infrastructure


def _internal_module(name: str) -> object:
    return importlib.import_module(
        f"tokdown.infrastructure._internal.{name}",
    )


# ---------- create_encoder function-level tests ----------


def test_tiktoken_create_encoder_returns_tiktoken_encoder() -> None:
    mod = _internal_module("tiktoken_encoder")
    encoder = mod.create_encoder("cl100k_base")
    assert type(encoder).__name__ == "TiktokenEncoder"


def test_tiktoken_create_encoder_import_error_has_clear_message() -> None:
    import builtins

    real_import = builtins.__import__

    def _block_tiktoken(name: str, *args: object, **kwargs: object) -> object:
        if name == "tiktoken":
            raise ImportError("No module named 'tiktoken'")
        return real_import(name, *args, **kwargs)

    mod = _internal_module("tiktoken_encoder")
    importlib.reload(mod)

    with patch("builtins.__import__", side_effect=_block_tiktoken):
        with pytest.raises(ImportError, match="uv add tiktoken"):
            mod.create_encoder("cl100k_base")


def test_huggingface_create_encoder_import_error_has_clear_message() -> None:
    import builtins

    real_import = builtins.__import__

    def _block_transformers(name: str, *args: object, **kwargs: object) -> object:
        if name == "transformers" or name.startswith("transformers."):
            raise ImportError("No module named 'transformers'")
        return real_import(name, *args, **kwargs)

    mod = _internal_module("huggingface_encoder")
    importlib.reload(mod)

    with patch("builtins.__import__", side_effect=_block_transformers):
        with pytest.raises(ImportError, match="uv add transformers"):
            mod.create_encoder("google/gemma-2-2b")


# ---------- token_encoder_factory.py must be deleted ----------


def test_token_encoder_factory_module_deleted() -> None:
    factory_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "tokdown"
        / "infrastructure"
        / "_internal"
        / "token_encoder_factory.py"
    )
    assert not factory_path.exists(), (
        "token_encoder_factory.py should be deleted"
    )


# ---------- sizing_factory routes by provider directly ----------


def test_sizing_factory_routes_openai_without_abstract_base() -> None:
    factory = create_infrastructure().chunk_sizer_factory
    sizer = factory.create_for(
        SizerConfig(
            unit=ChunkUnit.TOKENS,
            token_provider="openai",
            model_id="cl100k_base",
        ),
    )
    assert type(sizer.encoder).__name__ == "TiktokenEncoder"


def test_sizing_factory_unsupported_provider_raises() -> None:
    factory = create_infrastructure().chunk_sizer_factory
    with pytest.raises(
        NotImplementedError,
        match="unsupported token provider",
    ):
        factory.create_for(
            SizerConfig(
                unit=ChunkUnit.TOKENS,
                token_provider="bogus",
                model_id="whatever",
            ),
        )


# ---------- existing integration tests ----------


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


# ---------- stdout suppression (cached model) ----------


def test_tiktoken_cached_does_not_pollute_stdout(capsys) -> None:
    """When tiktoken encoding data is cached, nothing appears on stdout."""
    mod = _internal_module("tiktoken_encoder")
    # cl100k_base is always cached in CI / dev after first load
    mod.create_encoder("cl100k_base")

    captured = capsys.readouterr()
    assert captured.out == "", f"stdout polluted: {captured.out!r}"


@pytest.mark.slow
def test_huggingface_cached_does_not_pollute_stdout(capsys) -> None:
    """When HF model is cached locally, nothing appears on stdout."""
    mod = _internal_module("huggingface_encoder")
    try:
        mod.create_encoder("google/gemma-2-2b")
    except OSError as exc:
        _skip_if_hf_model_unavailable(exc)
        raise

    captured = capsys.readouterr()
    assert captured.out == "", f"stdout polluted: {captured.out!r}"


# ---------- offline + uncached → RuntimeError ----------


def test_tiktoken_offline_uncached_raises_runtime_error() -> None:
    """Tiktoken must raise RuntimeError when encoding is not cached and network
    is unavailable."""
    mod = _internal_module("tiktoken_encoder")
    importlib.reload(mod)

    import tiktoken

    def _fail_get_encoding(name):
        raise ConnectionError("Simulated network failure")

    # Clear in-memory cache so it actually tries to load
    tiktoken.registry.ENCODINGS.pop("fake_uncached_enc", None)

    with patch.object(tiktoken, "get_encoding", side_effect=_fail_get_encoding):
        with patch(
            f"{mod.__name__}._is_cached",
            return_value=False,
        ):
            with pytest.raises(
                RuntimeError,
                match="not cached and network is unavailable",
            ):
                mod.create_encoder("fake_uncached_enc")


def test_huggingface_offline_uncached_raises_runtime_error() -> None:
    """HuggingFace must raise RuntimeError when model is not cached and network
    is unavailable."""
    mod = _internal_module("huggingface_encoder")
    importlib.reload(mod)

    from transformers import AutoTokenizer

    with patch.object(
        AutoTokenizer,
        "from_pretrained",
        side_effect=OSError("Simulated network failure"),
    ):
        with pytest.raises(
            RuntimeError,
            match="not cached and network is unavailable",
        ):
            mod.create_encoder("fake/uncached-model")


# ---------- stdout_clean.py must be deleted ----------


def test_stdout_clean_module_deleted() -> None:
    stdout_clean_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "tokdown"
        / "interface"
        / "_internal"
        / "stdout_clean.py"
    )
    assert not stdout_clean_path.exists(), (
        "stdout_clean.py should be deleted — adapters handle their own suppression"
    )
