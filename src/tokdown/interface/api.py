from tokdown.interface._internal.cli import CliController


def main(argv: list[str] | None = None) -> int:
    """CLI entry: parse args, create infrastructure, run application."""
    return CliController(argv).run()
