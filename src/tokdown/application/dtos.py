from dataclasses import dataclass
from pathlib import Path

from tokdown.domain.api import ChunkLimit, ChunkUnit


@dataclass(frozen=True)
class SizerConfig:
    unit: ChunkUnit
    token_provider: str  # "" when unit is WORDS
    model_id: str  # "" when unit is WORDS


@dataclass(frozen=True)
class CountDocumentRequest:
    source_path: Path
    sizer_config: SizerConfig


@dataclass(frozen=True)
class CountDocumentResult:
    source_path: Path
    count: int


@dataclass(frozen=True)
class SplitDocumentRequest:
    source_path: Path
    limit: ChunkLimit
    token_provider: str
    model_id: str
    output_dir: Path | None
    force: bool = False


@dataclass(frozen=True)
class SplitDocumentResult:
    source_path: Path
    output_dir: Path
    part_count: int
    part_paths: tuple[Path, ...]
