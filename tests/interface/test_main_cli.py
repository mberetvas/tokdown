from pathlib import Path

from tokdown.interface.api import main


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


def test_words_mode_defaults_output_dir_to_source_parent(tmp_path: Path) -> None:
    source = tmp_path / "sample.md"
    source.write_text("alpha beta gamma delta", encoding="utf-8")

    exit_code = main(["--words", str(source), "2"])

    assert exit_code == 0
    assert (tmp_path / "sample_part1.md").exists()
    assert (tmp_path / "sample_part2.md").exists()
