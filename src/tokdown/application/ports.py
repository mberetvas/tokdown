from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from tokdown.application.dtos import SizerConfig
from tokdown.domain.api import ChunkSizer


@dataclass(frozen=True)
class MarkdownDocument:
    path: Path
    body: str

    @property
    def stem(self) -> str:
        return self.path.stem


@dataclass(frozen=True)
class DocumentPart:
    number: int
    body: str


class PartFileExistsError(Exception):
    """Raised when {stem}_part{n}.md exists and force=False."""


class ChunkSizerFactory(Protocol):
    def create_for(self, config: SizerConfig) -> ChunkSizer:
        """Create a chunk sizer for the given sizing configuration."""


class DocumentGateway(ABC):
    @abstractmethod
    def load(self, path: Path) -> MarkdownDocument:
        """Load a markdown document from disk."""

    @abstractmethod
    def save_part(
        self,
        document: MarkdownDocument,
        part: DocumentPart,
        directory: Path,
        *,
        force: bool,
    ) -> None:
        """Write a document part to disk."""
