import argparse
import sys
from pathlib import Path
from uuid import uuid4

from tokdown.application.api import (
    CountDocumentApplication,
    CountDocumentRequest,
    PartFileExistsError,
    SizerConfig,
    SplitDocumentApplication,
    SplitDocumentRequest,
)
from tokdown.domain.api import ChunkUnit, chunk_limit
from tokdown.domain.logging.api import LogLevel
from tokdown.infrastructure.api import (
    InfraSettings,
    Infrastructure,
    create_infrastructure,
)

from .stdout_clean import stdout_clean


def _normalize_argv(argv: list[str] | None) -> list[str]:
    effective = list(sys.argv[1:] if argv is None else argv)
    if not effective:
        return effective
    if effective[0] in ("count", "split"):
        return effective
    if effective[0] in ("-h", "--help"):
        return effective
    return ["split", *effective]


class CliController:
    def __init__(self, argv: list[str] | None = None) -> None:
        self._argv = argv

    def run(self) -> int:
        argv = _normalize_argv(self._argv)
        if argv and argv[0] in ("-h", "--help"):
            try:
                self._build_parent_parser().parse_args(argv)
            except SystemExit as exc:
                return exc.code if isinstance(exc.code, int) else 1
            return 0

        try:
            args = self._build_parser().parse_args(argv)
        except SystemExit as exc:
            return exc.code if isinstance(exc.code, int) else 1

        if args.command == "count":
            return self._run_count(args)
        return self._run_split(args)

    def _run_count(self, args: argparse.Namespace) -> int:
        sizer_config = _sizer_config_from_args(args)
        infrastructure = _create_infrastructure(args, sizer_config)
        application = CountDocumentApplication(
            document_gateway=infrastructure.document_gateway,
            chunk_sizer_factory=infrastructure.chunk_sizer_factory,
            logger=infrastructure.logger,
        )
        request = CountDocumentRequest(
            source_path=args.input_file,
            sizer_config=sizer_config,
        )
        try:
            with stdout_clean():
                result = application.execute(request)
        except FileNotFoundError:
            print(f"Input file not found: {args.input_file}", file=sys.stderr)
            return 1
        except OSError as exc:
            print(f"Failed to process document: {exc}", file=sys.stderr)
            return 1

        print(result.count)
        return 0

    def _run_split(self, args: argparse.Namespace) -> int:
        sizer_config = _sizer_config_from_args(args)
        infrastructure = _create_infrastructure(args, sizer_config)
        application = SplitDocumentApplication(
            document_gateway=infrastructure.document_gateway,
            chunk_sizer_factory=infrastructure.chunk_sizer_factory,
            splitting_domain=infrastructure.splitting_domain,
            logger=infrastructure.logger,
        )
        request = SplitDocumentRequest(
            source_path=args.input_file,
            limit=chunk_limit(args.limit, sizer_config.unit),
            token_provider=sizer_config.token_provider,
            model_id=sizer_config.model_id,
            output_dir=args.output_dir,
            force=args.force,
        )
        try:
            result = application.execute(request)
        except FileNotFoundError:
            print(f"Input file not found: {args.input_file}")
            return 1
        except PartFileExistsError as exc:
            print(exc)
            return 1
        except OSError as exc:
            print(f"Failed to process document: {exc}")
            return 1

        if not args.quiet:
            print(f"Wrote {result.part_count} part(s) to {result.output_dir}")
        return 0

    def _build_parent_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="tokdown",
            description=(
                "Split markdown documents into size-bounded parts, "
                "or count tokens/words before splitting."
            ),
        )
        subparsers = parser.add_subparsers(dest="command")
        subparsers.add_parser(
            "count",
            help="Print token or word count for a document (stdout: integer only).",
        )
        subparsers.add_parser(
            "split",
            help="Split a document into size-bounded parts.",
        )
        return parser

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="tokdown",
            description=(
                "Split markdown documents into size-bounded parts, "
                "or count tokens/words before splitting."
            ),
        )
        subparsers = parser.add_subparsers(dest="command", required=True)

        count_parser = subparsers.add_parser(
            "count",
            help="Print token or word count for a document (stdout: integer only).",
        )
        _add_sizing_flags(count_parser)
        _add_logging_flags(count_parser)
        count_parser.add_argument("input_file", type=Path)

        split_parser = subparsers.add_parser(
            "split",
            help="Split a document into size-bounded parts.",
        )
        _add_sizing_flags(split_parser)
        _add_logging_flags(split_parser)
        split_parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing part files.",
        )
        split_parser.add_argument(
            "--quiet",
            action="store_true",
            help="Suppress success messages on stdout.",
        )
        split_parser.add_argument("input_file", type=Path)
        split_parser.add_argument("limit", type=int)
        split_parser.add_argument("output_dir", type=Path, nargs="?", default=None)
        return parser


def _sizer_config_from_args(args: argparse.Namespace) -> SizerConfig:
    if args.words:
        return SizerConfig(unit=ChunkUnit.WORDS, token_provider="", model_id="")
    token_provider = args.provider
    if args.provider == "openai":
        model_id = args.model_id or "cl100k_base"
    else:
        model_id = args.model_id or "google/gemma-2-2b"
    return SizerConfig(
        unit=ChunkUnit.TOKENS,
        token_provider=token_provider,
        model_id=model_id,
    )


def _create_infrastructure(
    args: argparse.Namespace,
    sizer_config: SizerConfig,
) -> Infrastructure:
    return create_infrastructure(
        InfraSettings(
            log_level=LogLevel(args.log_level),
            log_format=args.log_format,
            correlation_id=str(uuid4()),
            token_provider=sizer_config.token_provider,
        ),
    )


def _add_sizing_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--words",
        action="store_true",
        help="Measure or split by word count instead of tokens.",
    )
    parser.add_argument(
        "--provider",
        choices=["openai", "google"],
        default="google",
        help="Token provider (default: google).",
    )
    parser.add_argument(
        "-m",
        "--model",
        dest="model_id",
        default=None,
        help=(
            "Model or encoding id "
            "(google: google/gemma-2-2b, openai: cl100k_base)."
        ),
    )


def _add_logging_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--log-level",
        choices=[level.value for level in LogLevel],
        default=LogLevel.INFO.value,
        help="Minimum log level to emit.",
    )
    parser.add_argument(
        "--log-format",
        choices=["json", "text"],
        default="text",
        help="Log output format (stderr).",
    )
