################
# Created/Changed using: Crush/gpt-6.1-sol
# HUMAN VERIFICATION: quick glance, lgtm
################
"""Basic command-line interface tests."""

from importlib.resources import files
from pathlib import Path

import pytest

from analog_daddy.__main__ import ai, app


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ([], "For agent skill discovery"),
        (["--help"], "ai"),
        (["ai", "--help"], "--copy"),
        (["ai"], "Bundled skill directory:"),
    ],
)
def test_cli_output(
    arguments: list[str],
    expected: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Basic commands succeed and display useful output."""
    with pytest.raises(SystemExit) as result:
        app(arguments)

    assert result.value.code == 0
    captured = capsys.readouterr()
    assert expected in captured.out
    assert captured.err == ""


@pytest.mark.parametrize("explicit_destination", [False, True])
def test_ai_copy(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    explicit_destination: bool,
) -> None:
    """
    Copy the bundled skill to the current or specified parent directory.
    """
    monkeypatch.chdir(tmp_path)
    arguments = ["ai", "--copy"]
    destination = tmp_path
    if explicit_destination:
        destination = tmp_path / "skills"
        arguments.extend(["--destination", str(destination)])

    with pytest.raises(SystemExit) as result:
        app(arguments)

    assert result.value.code == 0
    target = destination / "analog-daddy"
    source = files("analog_daddy") / "clanker"
    assert (target / "SKILL.md").read_text() == (
        source / "SKILL.md"
    ).read_text()
    assert (target / "references" / "notebook" / "doctests.py").is_file()
    assert not list(target.rglob("__pycache__"))
    assert not list(target.rglob(".*"))


def test_ai_copy_preserves_existing_destination(tmp_path: Path) -> None:
    """An existing skill directory is not overwritten."""
    target = tmp_path / "analog-daddy"
    target.mkdir()
    skill = target / "SKILL.md"
    skill.write_text("Existing skill")

    with pytest.raises(FileExistsError):
        ai(copy=True, destination=tmp_path)

    assert skill.read_text() == "Existing skill"
