"""Tests for ChunkSizer.hard_split implementations."""

from dataclasses import dataclass
import importlib

from tokdown.domain.api import WordChunkSizer

TokenChunkSizer = importlib.import_module(
    "tokdown.infrastructure._internal.token_chunk_sizer",
).TokenChunkSizer
# ── Fake encoder for deterministic token tests ──────────────────────


@dataclass(frozen=True)
class FakeTokenEncoder:
    """Each whitespace-separated word = 1 token (id = hash)."""

    def encode(self, text: str) -> list[int]:
        if not text or not text.strip():
            return []
        return [hash(w) & 0xFFFF for w in text.split()]

    def decode(self, token_ids: list[int]) -> str:
        # Not a real inverse — tests that need decode build a reversible map.
        raise NotImplementedError("use AsymmetricEncoder for decode tests")


@dataclass(frozen=True)
class AsymmetricEncoder:
    """Encode splits on whitespace; decode joins with a *double* space.

    This makes ``decode(encode(t))`` differ from ``t``, which is exactly
    the asymmetry that triggered the old round-trip assertion bug.
    """

    def encode(self, text: str) -> list[int]:
        if not text or not text.strip():
            return []
        return [hash(w) & 0xFFFF for w in text.split()]

    def decode(self, token_ids: list[int]) -> str:
        # Return a string whose re-encode length *may* differ from len(token_ids).
        # We just produce one "word" per id so re-encoding is still predictable,
        # but the decoded text is different from the original.
        return "  ".join(f"t{tid}" for tid in token_ids)


# ── WordChunkSizer.hard_split ────────────────────────────────────────


class TestWordChunkSizerHardSplit:
    def test_splits_text_into_word_bounded_chunks(self) -> None:
        sizer = WordChunkSizer()
        result = sizer.hard_split("one two three four", 2)
        assert result == ["one two", "three four"]

    def test_single_chunk_when_under_limit(self) -> None:
        sizer = WordChunkSizer()
        result = sizer.hard_split("hello world", 10)
        assert result == ["hello world"]

    def test_empty_text_returns_single_empty_string(self) -> None:
        sizer = WordChunkSizer()
        result = sizer.hard_split("", 5)
        assert result == [""]

    def test_whitespace_only_returns_single_empty_string(self) -> None:
        sizer = WordChunkSizer()
        result = sizer.hard_split("   ", 5)
        assert result == [""]

    def test_exact_limit_boundary(self) -> None:
        sizer = WordChunkSizer()
        result = sizer.hard_split("a b c d e f", 3)
        assert result == ["a b c", "d e f"]

    def test_remainder_chunk(self) -> None:
        sizer = WordChunkSizer()
        result = sizer.hard_split("a b c d e", 2)
        assert result == ["a b", "c d", "e"]


# ── TokenChunkSizer.hard_split ───────────────────────────────────────


@dataclass(frozen=True)
class ReversibleTokenEncoder:
    """Reversible fake: word → id via lookup table, decode via reverse lookup."""

    _words: tuple[str, ...] = ()
    _word_to_id: dict[str, int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        table = {w: i for i, w in enumerate(self._words)}
        object.__setattr__(self, "_word_to_id", table)

    def encode(self, text: str) -> list[int]:
        if not text or not text.strip():
            return []
        return [self._word_to_id[w] for w in text.split()]

    def decode(self, token_ids: list[int]) -> str:
        return " ".join(self._words[tid] for tid in token_ids)


class TestTokenChunkSizerHardSplit:
    def _make_sizer(self, words: tuple[str, ...]) -> TokenChunkSizer:
        encoder = ReversibleTokenEncoder(_words=words)
        return TokenChunkSizer(encoder=encoder)

    def test_splits_token_ids_by_limit(self) -> None:
        sizer = self._make_sizer(("one", "two", "three", "four"))
        result = sizer.hard_split("one two three four", 2)
        assert result == ["one two", "three four"]

    def test_single_chunk_when_under_limit(self) -> None:
        sizer = self._make_sizer(("hello", "world"))
        result = sizer.hard_split("hello world", 10)
        assert result == ["hello world"]

    def test_empty_text_returns_single_empty_string(self) -> None:
        sizer = self._make_sizer(())
        result = sizer.hard_split("", 5)
        assert result == [""]

    def test_remainder_chunk(self) -> None:
        sizer = self._make_sizer(("a", "b", "c", "d", "e"))
        result = sizer.hard_split("a b c d e", 2)
        assert result == ["a b", "c d", "e"]

    def test_no_round_trip_assertion_with_asymmetric_encoder(self) -> None:
        """The old code crashed here because decode→encode is asymmetric.

        The new implementation must NOT assert round-trip equality — it
        trusts the token-ID slice, which is correct by construction.
        """
        encoder = AsymmetricEncoder()
        sizer = TokenChunkSizer(encoder=encoder)
        # 4 "tokens", limit 2 → should produce 2 chunks without crashing
        result = sizer.hard_split("alpha beta gamma delta", 2)
        assert len(result) == 2
