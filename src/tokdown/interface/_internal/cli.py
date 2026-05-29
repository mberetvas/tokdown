import argparse
from pathlib import Path

from tokdown.application.api import (
    PartFileExistsError,
    SplitDocumentApplication,
    SplitDocumentRequest,
)
from tokdown.domain.api import ChunkUnit, chunk_limit
from tokdown.infrastructure.api import InfraSettings, create_infrastructure


class CliController:
    def __init__(self, argv: list[str] | None = None) -> None:
        self._argv = argv

    def run(self) -> int:
        args = self._parse_args()
        if args.words:
            unit = ChunkUnit.WORDS
            token_provider = ""
            model_id = ""
        else:
            unit = ChunkUnit.TOKENS
            token_provider = args.provider
            if args.provider == "openai":
                model_id = args.model_id or "cl100k_base"
            else:
                model_id = args.model_id or "google/gemma-2-2b"

        infrastructure = create_infrastructure(InfraSettings())
        application = SplitDocumentApplication(
            document_gateway=infrastructure.document_gateway,
            chunk_sizer_factory=infrastructure.chunk_sizer_factory,
            splitting_domain=infrastructure.splitting_domain,
            logger=infrastructure.logger,
        )
        request = SplitDocumentRequest(
            source_path=args.input_file,
            limit=chunk_limit(args.limit, unit),
            token_provider=token_provider,
            model_id=model_id,
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

        print(f"Wrote {result.part_count} part(s) to {result.output_dir}")
        return 0

    def _parse_args(self) -> argparse.Namespace:
        parser = argparse.ArgumentParser(prog="tokdown")
        parser.add_argument(
            "--words",
            action="store_true",
            help="Split by word count instead of tokens.",
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
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing part files.",
        )
        parser.add_argument("input_file", type=Path)
        parser.add_argument("limit", type=int)
        parser.add_argument("output_dir", type=Path, nargs="?", default=None)
        return parser.parse_args(self._argv)
