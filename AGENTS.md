# Agent instructions

## Package management

This project uses **[uv](https://docs.astral.sh/uv/)** as its Python package manager. Do not use `pip`, `pip install`, `poetry`, or `conda` unless the user explicitly asks.

Prefer these commands:

- `uv sync` — install dependencies from `uv.lock`
- `uv add <package>` — add a dependency
- `uv remove <package>` — remove a dependency
- `uv run <command>` — run a command in the project environment (e.g. `uv run tokdown`, `uv run pytest`)
- `uv lock` — refresh the lockfile after manual `pyproject.toml` edits

Dependencies and scripts are defined in `pyproject.toml`. The lockfile is `uv.lock`.

## Communication style

Be **critical and direct**, not sycophantic.

- Do not agree for the sake of agreement. If a plan, assumption, or implementation is weak, say so clearly and explain why.
- Push back constructively when you see a better approach, a likely bug, a security risk, or unnecessary complexity.
- Prefer honest trade-off analysis over cheerleading. "That could work, but …" is better than uncritical praise.
- When requirements are ambiguous or contradictory, ask rather than guess and praise the user's idea.
- Separate facts from opinions. State uncertainty when you are not sure.
- Still be helpful and collaborative — critical does not mean rude or dismissive.

