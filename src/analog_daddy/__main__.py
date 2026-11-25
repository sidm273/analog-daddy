"""analog-daddy command-line interface."""

from importlib.resources import as_file, files
from pathlib import Path
from shutil import copytree, ignore_patterns

import cyclopts
import rich.console

app = cyclopts.App()
console = rich.console.Console()


@app.default
def main() -> None:
    """Console script for analog_daddy."""
    console.print(":construction: Construction in progress... :warning:")
    console.print("For agent skill discovery, run: analog_daddy ai --help")


@app.command
def ai(copy: bool = False, destination: Path = Path()) -> None:
    """
    Displays the bundled agent skill directory and optionally copy it.

    An AI agent should utilize it to reference the bundled agent skill
    without having to install it. Can optionally be installed into the
    provided directory.
    """
    skill = files(__package__) / "clanker"
    console.print(f"Bundled skill directory: {skill}")
    if copy:
        target = destination / "analog-daddy"
        with as_file(skill) as source:
            copytree(
                source,
                target,
                ignore=ignore_patterns("__pycache__", "*.pyc", ".*"),
            )
        console.print(f"Copied skill to {target}")


if __name__ == "__main__":
    app()
