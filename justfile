# Justfile for analog-daddy

python_version := "3.14"

default:
    just --choose

alias b := build
alias c := clean
alias d := docs-serve
alias t := test
alias m := marimo

marimo notebook="src/analog_daddy/drafts.py":
    # Launch marimo notebook
    uv run marimo --log-level info edit \
        --headless --no-token --skip-update-check \
        --no-sandbox {{ notebook }}

qa:
    # Run pre-commit hooks using prek.
    uv run prek run

testall:
    # Run all the tests for all the supported Python versions
    uv run --python=3.12 pytest
    uv run --python=3.13 pytest
    uv run --python={{ python_version }} pytest

test *ARGS:
    # Run all the tests, but allow for arguments to be passed
    @echo "Running with arg: {{ ARGS }}"
    uv run --python={{ python_version }} pytest {{ ARGS }}

docs-serve:
    # Serve docs locally with live reload
    -lsof -ti :8000 | xargs kill
    uv run --group docs zensical serve

docs-build:
    # Build docs (strict mode, fails on warnings)
    uv run --group docs zensical build --clean

build:
    # Build the project, useful for checking that packaging is correct
    rm -rf build
    rm -rf dist
    uv build

release:
    # Tag, push, and create a GitHub release
    uv run scripts/release.py

clean *ARGS:
    # Remove all build, test and Python artifacts
    ./scripts/clean_cache.py {{ ARGS }}

publish:
    # Publish to PyPI (manual alternative to GitHub Actions)
    uv build
    uv publish

# just version-bump [dev|alpha|beta|patch|minor|major]
version-bump bump="dev":
    #!/usr/bin/env bash
    set -euo pipefail
    uv version --bump {{ bump }}
    tag="v$(uv version --short)"
    git add pyproject.toml uv.lock
    git commit --message "Release $tag"
    git tag --annotate "$tag" --message "Release $tag"
    just _push

[confirm("Push the release?")]
_push:
    # push with tags.
    git push origin HEAD --tags --verbose
