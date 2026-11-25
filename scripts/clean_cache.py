#!/usr/bin/env --split-string=uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["cyclopts>=3", "rich"]
# ///
################
# Created/Changed using: Crush / GPT-6.1-sol
# HUMAN VERIFICATION: LGTM
################
"""
Remove build artifacts and caches, previewing changes unless --apply is
set.

Run ``uv run clean_cache.py [directory]`` to preview, then add
``--apply`` to delete. ROOT_PATTERNS match only the selected directory's
children; CACHE_PATTERNS match basenames recursively. Symlinks are never
traversed.
"""

import os
import shutil
from fnmatch import fnmatchcase
from pathlib import Path

from cyclopts import App
from rich.console import Console

ROOT_PATTERNS: tuple[str, ...] = (
    "build",
    "dist",
    ".eggs",
    ".pytest_cache",
    ".hypothesis",
    "site",
    ".cache",
    ".complexipy_cache",
)
CACHE_PATTERNS: tuple[str, ...] = (
    "*.egg-info",
    "*.egg",
    "*.pyc",
    "*.pyo",
    "*~",
    "__pycache__",
    ".rumdl_cache",
    ".ruff_cache",
)

app = App(help=__doc__)
console = Console(markup=False, highlight=False)


def fail_walk(error: OSError) -> None:
    """
    Report inaccessible directories rather than silently skipping them.
    """
    raise error


def remove_artifact(path: Path) -> None:
    """Delete an artifact without following symlinks."""
    if path.is_symlink() or not path.is_dir():
        path.unlink()
    else:
        shutil.rmtree(path)


def clean_parent(
    parent: Path,
    directories: list[str],
    files: list[str],
    patterns: tuple[str, ...],
    *,
    apply: bool,
) -> None:
    """Process matching children and prune them from traversal."""
    for name in directories.copy() + files:
        if not any(fnmatchcase(name, pattern) for pattern in patterns):
            continue
        path = parent / name
        if name in directories:
            directories.remove(name)
        console.print("Delete" if apply else "Would delete", str(path))
        if apply:
            remove_artifact(path)


@app.default
def main(directory: Path = Path(), *, apply: bool = False) -> None:
    """
    Preview matching artifacts, or permanently delete them with --apply.
    """
    root = directory.resolve(strict=True)
    if not root.is_dir():
        message = f"Not a directory: {root}"
        raise NotADirectoryError(message)
    if root in (Path(root.anchor), Path.home().resolve()):
        message = "Refusing to clean a filesystem root or your home directory."
        raise ValueError(message)

    for parent, directories, files in os.walk(root, onerror=fail_walk):
        directories[:] = [name for name in directories if name != ".venv"]
        parent_path = Path(parent)
        patterns = CACHE_PATTERNS
        if parent_path == root:
            patterns += ROOT_PATTERNS
        clean_parent(parent_path, directories, files, patterns, apply=apply)


if __name__ == "__main__":
    app()
