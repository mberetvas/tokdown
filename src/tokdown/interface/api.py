from tokdown.interface._internal.composition import run_cli  # noqa: TID251


def main(argv: list[str] | None = None) -> int:
    """CLI entry: parse args, create infrastructure, run application."""
    return run_cli(argv)


__all__ = ["main"]
