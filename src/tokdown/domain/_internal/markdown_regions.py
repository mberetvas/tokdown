import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum

FENCE_LINE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


class RegionKind(Enum):
    PROSE = "prose"
    FENCE = "fence"
    FRONTMATTER = "frontmatter"


@dataclass(frozen=True)
class FenceInfo:
    indent: str
    marker_char: str
    marker_len: int
    info_string: str


@dataclass(frozen=True)
class MarkdownRegion:
    kind: RegionKind
    text: str
    fence: FenceInfo | None = None


def parse_fence_line(line: str) -> FenceInfo | None:
    """Return fence metadata when line opens or closes a fence."""
    stripped = line.rstrip("\r\n").rstrip(" \t")
    match = FENCE_LINE.match(stripped)
    if match is None:
        return None

    indent, marker, info_string = match.groups()
    return FenceInfo(
        indent=indent,
        marker_char=marker[0],
        marker_len=len(marker),
        info_string=info_string,
    )


def is_closing_fence(line: str, opening: FenceInfo) -> bool:
    parsed = parse_fence_line(line)
    if parsed is None:
        return False
    return (
        parsed.marker_char == opening.marker_char
        and parsed.marker_len == opening.marker_len
    )


def _is_frontmatter_delimiter(line: str) -> bool:
    return line.rstrip("\r").rstrip() == "---"


def _find_frontmatter_close(lines: list[str]) -> int | None:
    for i in range(1, len(lines)):
        if _is_frontmatter_delimiter(lines[i]):
            return i
    return None


def iter_regions(text: str) -> Iterator[MarkdownRegion]:
    """Yield prose, fenced, and frontmatter regions in document order."""
    if not text:
        yield MarkdownRegion(kind=RegionKind.PROSE, text="")
        return

    lines = text.split("\n")
    start_index = 0

    if _is_frontmatter_delimiter(lines[0]):
        closing = _find_frontmatter_close(lines)
        if closing is not None:
            yield MarkdownRegion(
                kind=RegionKind.FRONTMATTER,
                text="\n".join(lines[: closing + 1]),
            )
            start_index = closing + 1

    prose_lines: list[str] = []
    fence_lines: list[str] = []
    open_fence: FenceInfo | None = None

    def flush_prose() -> MarkdownRegion | None:
        if not prose_lines:
            return None
        text = "\n".join(prose_lines)
        prose_lines.clear()
        if not text:
            return None
        return MarkdownRegion(
            kind=RegionKind.PROSE,
            text=text,
        )

    for line in lines[start_index:]:
        if open_fence is None:
            parsed = parse_fence_line(line)
            if parsed is not None:
                prose_region = flush_prose()
                if prose_region is not None:
                    yield prose_region
                open_fence = parsed
                fence_lines = [line]
            else:
                prose_lines.append(line)
            continue

        fence_lines.append(line)
        if is_closing_fence(line, open_fence):
            yield MarkdownRegion(
                kind=RegionKind.FENCE,
                text="\n".join(fence_lines),
                fence=open_fence,
            )
            open_fence = None
            fence_lines = []

    if open_fence is not None:
        yield MarkdownRegion(
            kind=RegionKind.FENCE,
            text="\n".join(fence_lines),
            fence=open_fence,
        )
        return

    prose_region = flush_prose()
    if prose_region is not None:
        yield prose_region
