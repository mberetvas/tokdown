from dataclasses import dataclass
from uuid import uuid4

from tokdown.application.ports import DocumentGateway
from tokdown.domain.api import DocumentSplittingDomain
from tokdown.domain.logging.api import LogLevel, StructuredLogger

from .filesystem_gateway import FileSystemDocumentGateway
from .logging.factory import create_structured_logger
from .sizing_factory import ChunkSizerFactory


@dataclass(frozen=True)
class InfraSettings:
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "text"
    correlation_id: str = ""
    token_provider: str = ""


@dataclass(frozen=True)
class Infrastructure:
    settings: InfraSettings
    document_gateway: DocumentGateway
    chunk_sizer_factory: ChunkSizerFactory
    logger: StructuredLogger
    splitting_domain: DocumentSplittingDomain


def create_infrastructure(settings: InfraSettings | None = None) -> Infrastructure:
    effective_settings = settings or InfraSettings(correlation_id=str(uuid4()))
    logger = create_structured_logger(
        log_level=effective_settings.log_level,
        log_format=effective_settings.log_format,
        correlation_id=effective_settings.correlation_id,
        token_provider=effective_settings.token_provider,
    )
    return Infrastructure(
        settings=effective_settings,
        document_gateway=FileSystemDocumentGateway(),
        chunk_sizer_factory=ChunkSizerFactory(),
        logger=logger,
        splitting_domain=DocumentSplittingDomain(logger=logger),
    )
