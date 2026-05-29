from .cli import CliController


def run_cli(argv: list[str] | None = None) -> int:
    return CliController(argv).run()
