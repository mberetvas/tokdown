import json
import subprocess
from pathlib import Path

import pytest

from tokdown.interface.api import main

_REPO_ROOT = Path(__file__).resolve().parents[2]
_BANNER_FIRST_LINE = (
    _REPO_ROOT / "docs" / "assets" / "tokdown_ascii.txt"
).read_text(encoding="utf-8").splitlines()[0]


def test_words_mode_splits_file_and_writes_parts(tmp_path: Path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("one two three\n\nfour five six", encoding="utf-8")
    output_dir = tmp_path / "output"

    exit_code = main(["--words", str(source), "3", str(output_dir)])

    assert exit_code == 0
    part_one = (output_dir / "sample_part1.md").read_text(encoding="utf-8")
    part_two = (output_dir / "sample_part2.md").read_text(encoding="utf-8")
    assert part_one == "one two three"
    assert part_two == "four five six"


def test_openai_mode_splits_file_by_token_count(tmp_path: Path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("one two three\n\nfour five six", encoding="utf-8")
    output_dir = tmp_path / "output"

    argv = [
        "--provider",
        "openai",
        "-m",
        "cl100k_base",
        str(source),
        "3",
        str(output_dir),
    ]
    exit_code = main(argv)

    assert exit_code == 0
    part_one = (output_dir / "sample_part1.md").read_text(encoding="utf-8")
    part_two = (output_dir / "sample_part2.md").read_text(encoding="utf-8")
    assert part_one == "one two three"
    assert part_two == "four five six"


def test_words_mode_does_not_import_heavy_tokenizers(tmp_path: Path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("one two three", encoding="utf-8")
    code = f"""
import json
import sys
from tokdown.interface.api import main

exit_code = main(["--words", {str(source)!r}, "2"])
assert exit_code == 0
print(
    json.dumps(
        {{
            "transformers": "transformers" in sys.modules,
            "tiktoken": "tiktoken" in sys.modules,
        }}
    )
)
"""
    completed = subprocess.run(
        ["uv", "run", "python", "-c", code],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    loaded = json.loads(completed.stdout.strip().splitlines()[-1])
    assert loaded == {"transformers": False, "tiktoken": False}


@pytest.mark.slow
def test_google_mode_splits_file_by_token_count(tmp_path: Path) -> None:
    from tokdown.application.dtos import SizerConfig
    from tokdown.domain.api import ChunkUnit
    from tokdown.infrastructure.api import create_infrastructure

    model_id = "google/gemma-2-2b"
    factory = create_infrastructure().chunk_sizer_factory
    try:
        sizer = factory.create_for(
            SizerConfig(
                unit=ChunkUnit.TOKENS,
                token_provider="google",
                model_id=model_id,
            ),
        )
    except OSError as exc:
        if "gated repo" in str(exc).lower() or "restricted" in str(exc).lower():
            pytest.skip("google/gemma-2-2b requires Hugging Face access and cache")
        raise
    limit = sizer.measure("one two three")

    source = tmp_path / "sample.md"
    source.write_text("one two three\n\nfour five six", encoding="utf-8")
    output_dir = tmp_path / "output"

    argv = [
        "--provider",
        "google",
        "-m",
        model_id,
        str(source),
        str(limit),
        str(output_dir),
    ]
    exit_code = main(argv)

    assert exit_code == 0
    part_one = (output_dir / "sample_part1.md").read_text(encoding="utf-8")
    part_two = (output_dir / "sample_part2.md").read_text(encoding="utf-8")
    assert part_one == "one two three"
    assert part_two == "four five six"


def test_words_mode_defaults_output_dir_to_source_parent(tmp_path: Path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("alpha beta gamma delta", encoding="utf-8")

    exit_code = main(["--words", str(source), "2"])

    assert exit_code == 0
    assert (tmp_path / "sample_part1.md").exists()
    assert (tmp_path / "sample_part2.md").exists()


def test_cli_exits_one_when_part_file_exists_without_force(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "sample.md"
    source.write_text("one two three", encoding="utf-8")
    output_dir = tmp_path / "output"
    main(["--words", str(source), "3", str(output_dir)])

    exit_code = main(["--words", str(source), "3", str(output_dir)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Part file already exists" in captured.out
    assert "Traceback" not in captured.err


def test_quiet_suppresses_success_stdout(tmp_path: Path, capsys) -> None:
    source = tmp_path / "sample.md"
    source.write_text("one two three", encoding="utf-8")

    exit_code = main(["--words", "--quiet", str(source), "3"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""


def test_log_format_json_emits_output_file_exists_event(
    tmp_path: Path,
    capsys,
) -> None:
    import json

    source = tmp_path / "sample.md"
    source.write_text("one two three", encoding="utf-8")
    output_dir = tmp_path / "output"
    main(["--words", str(source), "3", str(output_dir)])

    exit_code = main(
        [
            "--words",
            "--log-format",
            "json",
            "--log-level",
            "error",
            str(source),
            "3",
            str(output_dir),
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    record = json.loads(captured.err.strip())
    assert record["event"] == "output_file_exists"
    assert record["correlation_id"]
    assert record["token_provider"] == ""


def test_log_format_text_emits_human_readable_event(
    tmp_path: Path,
    capsys,
) -> None:
    source = tmp_path / "sample.md"
    source.write_text("one two three", encoding="utf-8")
    output_dir = tmp_path / "output"
    main(["--words", str(source), "3", str(output_dir)])

    exit_code = main(
        [
            "--words",
            "--log-format",
            "text",
            "--log-level",
            "error",
            str(source),
            "3",
            str(output_dir),
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "event=output_file_exists" in captured.err


def test_cli_overwrites_existing_parts_with_force(tmp_path: Path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("alpha beta gamma delta", encoding="utf-8")
    output_dir = tmp_path / "output"
    main(["--words", str(source), "2", str(output_dir)])

    exit_code = main(
        ["--words", "--force", str(source), "1", str(output_dir)],
    )

    assert exit_code == 0
    assert (output_dir / "sample_part1.md").read_text(encoding="utf-8") == "alpha"
    assert len(list(output_dir.glob("sample_part*.md"))) == 4


def test_count_words_prints_integer_only(tmp_path: Path, capsys) -> None:
    source = tmp_path / "sample.md"
    source.write_text("one two three\n\nfour five six", encoding="utf-8")

    exit_code = main(["count", "--words", str(source)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "6\n"
    assert captured.err == ""


def test_count_empty_file_prints_zero(tmp_path: Path, capsys) -> None:
    source = tmp_path / "empty.md"
    source.write_bytes(b"")

    exit_code = main(["count", "--words", str(source)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "0\n"


def test_count_whitespace_only_file_words_returns_zero(tmp_path: Path, capsys) -> None:
    source = tmp_path / "blank.md"
    source.write_text("   \n\t  \n", encoding="utf-8")

    exit_code = main(["count", "--words", str(source)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "0\n"


def test_count_missing_file_stderr_only_no_stdout(
    tmp_path: Path,
    capsys,
) -> None:
    missing = tmp_path / "missing.md"

    exit_code = main(["count", "--words", str(missing)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "Input file not found" in captured.err


def test_count_words_subprocess_does_not_import_heavy_tokenizers(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sample.md"
    source.write_text("one two three", encoding="utf-8")
    code = f"""
import json
import sys
from tokdown.interface.api import main

exit_code = main(["count", "--words", {str(source)!r}])
assert exit_code == 0
print(
    json.dumps(
        {{
            "transformers": "transformers" in sys.modules,
            "tiktoken": "tiktoken" in sys.modules,
        }}
    )
)
"""
    completed = subprocess.run(
        ["uv", "run", "python", "-c", code],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    loaded = json.loads(completed.stdout.strip().splitlines()[-1])
    assert loaded == {"transformers": False, "tiktoken": False}


def test_root_help_lists_count_and_split(capsys) -> None:
    exit_code = main(["--help"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "count" in captured.out
    assert "split" in captured.out
    assert _BANNER_FIRST_LINE in captured.out
    assert captured.out.index(_BANNER_FIRST_LINE) < captured.out.index("usage:")


def test_cli_module_does_not_import_stdout_clean() -> None:
    """cli.py must not import or reference stdout_clean — adapters own suppression."""
    import ast

    cli_path = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "tokdown"
        / "interface"
        / "_internal"
        / "cli.py"
    )
    source = cli_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(cli_path))

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and "stdout_clean" in node.module:
                pytest.fail("cli.py still imports stdout_clean")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "stdout_clean" in alias.name:
                    pytest.fail("cli.py still imports stdout_clean")


def test_count_openai_stdout_is_integer_only(tmp_path: Path, capsys) -> None:
    source = tmp_path / "sample.md"
    source.write_text("one two three", encoding="utf-8")

    exit_code = main(
        [
            "count",
            "--provider",
            "openai",
            "-m",
            "cl100k_base",
            str(source),
        ],
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == "3\n"
    assert all(line.isdigit() for line in captured.out.splitlines())
