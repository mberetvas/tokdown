from tokdown.domain._internal.markdown_regions import (
    RegionKind,
    iter_regions,
    parse_fence_line,
)


def test_iter_regions_detects_tilde_fence() -> None:
    text = "before\n\n~~~\ncode\n~~~\nafter"

    regions = list(iter_regions(text))

    assert [region.kind for region in regions] == [
        RegionKind.PROSE,
        RegionKind.FENCE,
        RegionKind.PROSE,
    ]
    assert regions[1].text == "~~~\ncode\n~~~"
    assert regions[1].fence is not None
    assert regions[1].fence.marker_char == "~"
    assert regions[1].fence.marker_len == 3


def test_parse_fence_line_allows_trailing_spaces() -> None:
    fence = parse_fence_line("```python   ")

    assert fence is not None
    assert fence.marker_char == "`"
    assert fence.marker_len == 3
    assert fence.info_string == "python"


def test_closing_fence_line_allows_trailing_spaces() -> None:
    text = "```python\nprint('hi')\n```   \n"

    regions = list(iter_regions(text))

    assert len(regions) == 1
    assert regions[0].kind is RegionKind.FENCE
    assert regions[0].text.endswith("```   ")


def test_iter_regions_preserves_info_string_with_spaces() -> None:
    text = "```bash script.sh\necho hi\n```"

    regions = list(iter_regions(text))

    assert len(regions) == 1
    assert regions[0].fence is not None
    assert regions[0].fence.info_string == "bash script.sh"


def test_iter_regions_supports_four_backtick_markers() -> None:
    text = "````\ncode\n````"

    regions = list(iter_regions(text))

    assert len(regions) == 1
    assert regions[0].kind is RegionKind.FENCE
    assert regions[0].fence is not None
    assert regions[0].fence.marker_len == 4


def test_malformed_fence_runs_until_eof() -> None:
    text = "intro\n```python\nnever closed\nstill code"

    regions = list(iter_regions(text))

    assert [region.kind for region in regions] == [
        RegionKind.PROSE,
        RegionKind.FENCE,
    ]
    assert regions[0].text == "intro"
    assert regions[1].text == "```python\nnever closed\nstill code"


def test_fence_with_inner_blank_lines_is_single_region() -> None:
    text = "```python\nline one\n\nline two\n```"

    regions = list(iter_regions(text))

    assert len(regions) == 1
    assert regions[0].kind is RegionKind.FENCE
    assert "\n\n" in regions[0].text


def test_iter_regions_detects_frontmatter_at_file_start() -> None:
    text = "---\ntitle: hello\n---\nsome content"

    regions = list(iter_regions(text))

    assert regions[0].kind is RegionKind.FRONTMATTER
    assert regions[0].text == "---\ntitle: hello\n---"
    assert regions[1].kind is RegionKind.PROSE
    assert "some content" in regions[1].text


def test_frontmatter_with_multiple_keys() -> None:
    text = "---\ntitle: hello\nauthor: world\ntags:\n  - one\n  - two\n---\n\ncontent"

    regions = list(iter_regions(text))

    assert regions[0].kind is RegionKind.FRONTMATTER
    assert "title: hello" in regions[0].text
    assert "author: world" in regions[0].text


def test_empty_frontmatter() -> None:
    text = "---\n---\ncontent"

    regions = list(iter_regions(text))

    assert regions[0].kind is RegionKind.FRONTMATTER
    assert regions[0].text == "---\n---"


def test_unclosed_frontmatter_treated_as_prose() -> None:
    text = "---\ntitle: hello\nno closing marker"

    regions = list(iter_regions(text))

    assert all(r.kind is not RegionKind.FRONTMATTER for r in regions)
    assert regions[0].kind is RegionKind.PROSE


def test_frontmatter_not_detected_after_content() -> None:
    text = "some content\n---\ntitle: hello\n---"

    regions = list(iter_regions(text))

    assert all(r.kind is not RegionKind.FRONTMATTER for r in regions)


def test_frontmatter_followed_by_fence() -> None:
    text = "---\ntitle: hello\n---\n\n```python\ncode\n```"

    regions = list(iter_regions(text))

    assert regions[0].kind is RegionKind.FRONTMATTER
    fence_regions = [r for r in regions if r.kind is RegionKind.FENCE]
    assert len(fence_regions) == 1
