from dataclasses import dataclass
from enum import Enum


class ChunkUnit(Enum):
    WORDS = "words"
    TOKENS = "tokens"


@dataclass(frozen=True)
class ChunkLimit:
    value: int
    unit: ChunkUnit
