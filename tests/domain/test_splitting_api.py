import pytest

import tokdown.domain.api as domain_api
from tokdown.domain.api import (
    ChunkUnit,
    DocumentSplittingDomain,
    WordChunkSizer,
    chunk_limit,
)


def test_split_returns_one_chunk_when_body_fits_limit() -> None:
    domain = DocumentSplittingDomain()
    sizer = WordChunkSizer()
    limit = chunk_limit(10, ChunkUnit.WORDS)
    body = "one two three"

    chunks = domain.split(body, limit, sizer)

    assert chunks == [body]


def test_split_returns_multiple_chunks_when_body_exceeds_limit() -> None:
    domain = DocumentSplittingDomain()
    sizer = WordChunkSizer()
    limit = chunk_limit(3, ChunkUnit.WORDS)
    body = "one two three\n\nfour five six"

    chunks = domain.split(body, limit, sizer)

    assert len(chunks) == 2
    assert all(sizer.measure(chunk) <= limit.value for chunk in chunks)
    assert "one two three" in chunks[0]
    assert "four five six" in chunks[1]


def test_split_hard_splits_oversized_paragraph_by_words() -> None:
    domain = DocumentSplittingDomain()
    sizer = WordChunkSizer()
    limit = chunk_limit(2, ChunkUnit.WORDS)
    body = "one two three four"

    chunks = domain.split(body, limit, sizer)

    assert chunks == ["one two", "three four"]


def test_prose_and_fence_under_limit_stays_single_part() -> None:
    domain = DocumentSplittingDomain()
    sizer = WordChunkSizer()
    limit = chunk_limit(100, ChunkUnit.WORDS)
    body = "intro paragraph\n\n```python\ncode line\n\nmore code\n```"

    chunks = domain.split(body, limit, sizer)

    assert chunks == [body]


def test_fence_with_inner_blank_lines_is_not_split_when_under_limit() -> None:
    domain = DocumentSplittingDomain()
    sizer = WordChunkSizer()
    limit = chunk_limit(50, ChunkUnit.WORDS)
    body = "```python\nfirst\n\nsecond\n```"

    chunks = domain.split(body, limit, sizer)

    assert chunks == [body]


def test_split_raises_value_error_when_limit_is_zero() -> None:
    domain = DocumentSplittingDomain()
    sizer = WordChunkSizer()
    limit = chunk_limit(0, ChunkUnit.WORDS)

    with pytest.raises(ValueError, match="chunk limit must be positive"):
        domain.split("some text", limit, sizer)


def test_split_raises_value_error_when_limit_is_negative() -> None:
    domain = DocumentSplittingDomain()
    sizer = WordChunkSizer()
    limit = chunk_limit(-5, ChunkUnit.WORDS)

    with pytest.raises(ValueError, match="chunk limit must be positive"):
        domain.split("some text", limit, sizer)


def test_split_returns_empty_string_list_for_empty_body() -> None:
    domain = DocumentSplittingDomain()
    sizer = WordChunkSizer()
    limit = chunk_limit(10, ChunkUnit.WORDS)

    assert domain.split("", limit, sizer) == [""]


def test_split_returns_empty_string_list_for_whitespace_only_body() -> None:
    domain = DocumentSplittingDomain()
    sizer = WordChunkSizer()
    limit = chunk_limit(10, ChunkUnit.WORDS)

    assert domain.split("   \n\t  ", limit, sizer) == [""]


def test_domain_api_exports_split_surface_only() -> None:
    forbidden = {
        "DocumentGateway",
        "TokenEncoderFactory",
        "TokenProvider",
        "MarkdownDocument",
        "DocumentPart",
    }
    assert forbidden.isdisjoint(set(domain_api.__all__))
