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
