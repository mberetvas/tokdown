import json
import subprocess
from pathlib import Path

import pytest

from tokdown.interface.api import main

_REPO_ROOT = Path(__file__).resolve().parents[2]


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
    from tokdown.application.dtos import SplitDocumentRequest
    from tokdown.domain.api import ChunkUnit, chunk_limit
    from tokdown.infrastructure.api import create_infrastructure

    model_id = "google/gemma-2-2b"
    factory = create_infrastructure().chunk_sizer_factory
    try:
        sizer = factory.create_for(
            SplitDocumentRequest(
                source_path=tmp_path / "sample.md",
                limit=chunk_limit(1, ChunkUnit.TOKENS),
                token_provider="google",
                model_id=model_id,
                output_dir=None,
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
