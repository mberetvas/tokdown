from dataclasses import dataclass

from tokdown.domain.logging.api import LogEvent, LogLevel, StructuredLogger

from .markdown_regions import FenceInfo, RegionKind, is_closing_fence, iter_regions
from .sizing import ChunkSizer
from .value_objects import ChunkLimit


@dataclass(frozen=True)
class SplittableUnit:
    text: str
    fence: FenceInfo | None = None
    is_frontmatter: bool = False


class MarkdownChunkingService:
    """Split markdown on paragraph boundaries while preserving fenced code."""

    def __init__(self, *, logger: StructuredLogger | None = None) -> None:
        self._logger = logger

    def split(self, body: str, limit: ChunkLimit, sizer: ChunkSizer) -> list[str]:
        if sizer.measure(body) <= limit.value:
            return [body]

        units = _split_into_units(body)
        chunks: list[str] = []
        current_parts: list[str] = []

        for unit in units:
            if unit.is_frontmatter:
                if (
                    sizer.measure(unit.text) > limit.value
                    and self._logger is not None
                ):
                    self._logger.event(
                        LogLevel.WARN,
                        LogEvent.FRONTMATTER_EXCEEDS_LIMIT,
                        frontmatter_size=sizer.measure(unit.text),
                        limit=limit.value,
                    )
                current_parts = [unit.text]
                continue

            if sizer.measure(unit.text) > limit.value:
                if current_parts:
                    chunks.append("\n\n".join(current_parts))
                    current_parts = []
                if unit.fence is not None:
                    chunks.extend(
                        _hard_split_fence_unit(
                            unit,
                            limit,
                            sizer,
                            self._logger,
                        )
                    )
                else:
                    chunks.extend(_hard_split(unit.text, limit, sizer))
                continue

            candidate_parts = (
                [*current_parts, unit.text] if current_parts else [unit.text]
            )
            candidate = "\n\n".join(candidate_parts)
            if current_parts and sizer.measure(candidate) > limit.value:
                chunks.append("\n\n".join(current_parts))
                current_parts = [unit.text]
            else:
                current_parts = candidate_parts

        if current_parts:
            chunks.append("\n\n".join(current_parts))

        return chunks if chunks else [""]


def _split_into_units(body: str) -> list[SplittableUnit]:
    units: list[SplittableUnit] = []
    for region in iter_regions(body):
        if region.kind is RegionKind.FRONTMATTER:
            units.append(SplittableUnit(text=region.text, is_frontmatter=True))
            continue
        if region.kind is RegionKind.PROSE:
            if not region.text:
                continue
            units.extend(
                SplittableUnit(text=part)
                for part in region.text.split("\n\n")
                if part != ""
            )
            continue
        units.append(SplittableUnit(text=region.text, fence=region.fence))
    return units


def _fence_marker_line(fence: FenceInfo, *, include_info: bool) -> str:
    marker = fence.marker_char * fence.marker_len
    info = fence.info_string if include_info else ""
    return f"{fence.indent}{marker}{info}"


def _fence_language(info_string: str) -> str:
    stripped = info_string.strip()
    if not stripped:
        return ""
    return stripped.split()[0]


def _hard_split_fence_unit(
    unit: SplittableUnit,
    limit: ChunkLimit,
    sizer: ChunkSizer,
    logger: StructuredLogger | None,
) -> list[str]:
    assert unit.fence is not None
    fence = unit.fence
    lines = unit.text.split("\n")
    opener = lines[0]
    has_closer = len(lines) > 1 and is_closing_fence(lines[-1], fence)
    body_lines = lines[1:-1] if has_closer else lines[1:]
    body = "\n".join(body_lines)
    closer = lines[-1] if has_closer else None

    inner_chunks = _hard_split(body, limit, sizer)
    if logger is not None:
        logger.event(
            LogLevel.WARN,
            LogEvent.CODE_BLOCK_HARD_SPLIT,
            fence_language=_fence_language(fence.info_string),
            marker=fence.marker_char * fence.marker_len,
        )

    open_line = _fence_marker_line(fence, include_info=True)
    close_line = _fence_marker_line(fence, include_info=False)
    total = len(inner_chunks)
    result: list[str] = []

    for index, inner in enumerate(inner_chunks):
        if index == 0:
            chunk = f"{opener}\n{inner}" if inner else opener
        else:
            chunk = f"\n{open_line}\n{inner}" if inner else f"\n{open_line}\n"

        if index < total - 1:
            chunk = f"{chunk}\n{close_line}\n"
        elif closer is not None:
            chunk = f"{chunk}\n{closer}"
        else:
            chunk = f"{chunk}\n{close_line}\n"

        result.append(chunk)

    return result


def _hard_split(text: str, limit: ChunkLimit, sizer: ChunkSizer) -> list[str]:
    return sizer.hard_split(text, limit.value)
