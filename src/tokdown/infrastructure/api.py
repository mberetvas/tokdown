from dataclasses import dataclass
from uuid import uuid4

from tokdown.application.ports import DocumentGateway
from tokdown.domain.api import DocumentSplittingDomain
from tokdown.domain.logging.api import LogLevel, StructuredLogger
from tokdown.infrastructure._internal.filesystem_gateway import (
    FileSystemDocumentGateway,
)
from tokdown.infrastructure._internal.logging.noop_logger import NoOpStructuredLogger
from tokdown.infrastructure._internal.sizing_factory import ChunkSizerFactory


@dataclass(frozen=True)
class InfraSettings:
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "text"
    correlation_id: str = ""


@dataclass(frozen=True)
class Infrastructure:
    settings: InfraSettings
    document_gateway: DocumentGateway
    chunk_sizer_factory: ChunkSizerFactory
    logger: StructuredLogger
    splitting_domain: DocumentSplittingDomain


def create_infrastructure(settings: InfraSettings | None = None) -> Infrastructure:
    effective_settings = settings or InfraSettings(correlation_id=str(uuid4()))
    return Infrastructure(
        settings=effective_settings,
        document_gateway=FileSystemDocumentGateway(),
        chunk_sizer_factory=ChunkSizerFactory(),
        logger=NoOpStructuredLogger(),
        splitting_domain=DocumentSplittingDomain(),
    )
