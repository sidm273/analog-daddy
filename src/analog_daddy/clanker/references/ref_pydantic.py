"""
Reference model of preferred Pydantic programming pattern.

Before creating new pydantic models, reuse the fields, validators,
config patterns and types defined here. Only introduce new Pydantic
features after exhausting what's available in this file and after
consulting the user.

When asked to model a CLI command, read the :class:`Ripgrep` docstrings.
"""

import time
from typing import Literal

from pydantic import (
    AliasGenerator,
    BaseModel,
    ConfigDict,
    DirectoryPath,
    Field,
    FilePath,
    NewPath,
    PositiveInt,
    validate_call,
)
from pydantic.alias_generators import to_camel
from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliPositionalArg,
    SettingsConfigDict,
)

from analog_daddy.units import Time

Extensions = Literal["zip", "tar.gz", "7z"]


class KitchenSink(BaseModel):
    """
    A reference model containing most used patterns.

    Key features include, customized serialization aliases, using custom
    types and its serialization preferences. Field docstrings serve as
    usage examples. Keep new field docstrings equally explicit.

    Examples
    --------
    >>> from pathlib import Path
    >>> x = KitchenSink(base_command="gh", directory=Path())
    >>> x.middle_name
    'Reginald'
    >>> x.custom_logpath
    '%J.out'
    >>> x.listicle
    [('item1', 1), ('item2', '2n')]
    >>> x.log_path is None
    True
    >>> x.model_dump()["base_command"]
    'gh'
    >>> x.model_dump(by_alias=True)["baseCommand"]
    'gh'
    >>> x.model_dump()["age"]
    30

    Direct construction validates fields too; ``n`` must be positive:

    >>> KitchenSink(base_command="gh", directory=Path(), n=0)
    Traceback (most recent call last):
    ...
    pydantic_core._pydantic_core.ValidationError: ...

    Validate input data with ``model_validate``:

    >>> validated = KitchenSink.model_validate(
    ...     {"base_command": "gh", "directory": Path()}
    ... )
    >>> validated.base_command
    'gh'

    Select fields with ``include`` or omit fields with ``exclude``:

    >>> x.model_dump(include={"base_command", "age"})
    {'base_command': 'gh', 'age': 30}
    >>> "age" in x.model_dump(exclude={"age"})
    False

    Time unit serialization can be selected through the serialization
    context:

    >>> x.model_dump()["start_time"]
    1e-09
    >>> x.model_dump(context={"quantity_format": "str"})["start_time"]
    '1 ns'
    >>> x.model_dump(context={"quantity_format": "as_tuple"})["start_time"]
    (1e-09, 's')

    Notes
    -----
    This is a collection of the pydantic features I find useful and want
    to encourage AI agents to use this as a building block. You can also
    utilize the official pydantic skill, however the agent sometimes
    utilizes advanced features of pydantic when unnecessary.
    """  # noqa: DOC601, DOC603

    model_config = ConfigDict(
        use_attribute_docstrings=True,
        alias_generator=AliasGenerator(
            serialization_alias=to_camel,
        ),
    )
    base_command: str
    sub_command: tuple[str, ...] = ("release", "download")
    middle_name: str = "Reginald"
    """Middle name of the person."""
    created_at: float = Field(default_factory=time.time)
    directory: DirectoryPath
    archive: Literal["zip", "tar.gz"] = "zip"
    acceptable_ext: list[Extensions] = Field(default=["zip"])
    """A list of acceptable extensions."""
    start_time: Time = Time("1n")
    log_path: FilePath | None = None
    n: PositiveInt = Field(default=2)
    age: int = Field(ge=0, le=150, default=30)
    """User age."""
    custom_logpath: NewPath | Literal["%J.out"] = "%J.out"
    """A custom new path field."""
    listicle: list[tuple[str, int | str]] = Field(
        default=[("item1", 1), ("item2", "2n")]
    )


class Ripgrep(BaseSettings):
    """
    Build command argument list using pydantic's serialization.

    Model a CLI command as a minimal, typed Pydantic model that
    serializes into ``list[str]`` for subprocess execution. Follow
    applicable type, configuration, field documentation, and
    serialization conventions documented in this reference class. Use
    provided CLI usage information (usually provided as command or a
    code which chains lists to create commands). If absent, consult
    ``tldr``, then ``--help``, then ``man`` pages. Stop once sufficient
    information is available. Model the requested subset of common
    options, flags, positional arguments, and subcommands. Do not invent
    missing requirements or cover every option. Use
    ``pydantic_settings.CliApp.serialize``; do not hand-roll flag
    serialization. Prefer ``BaseModel``; use ``BaseSettings`` only when
    environment-variable loading is requested. Document fields with
    attribute docstrings and enable ``use_attribute_docstrings=True``.
    Avoid exhaustive validation, obscure options, and special edge-case
    handling. Delegate semantic validation to the executable. Keep the
    model minimal, readable, and deterministic. Do not introduce
    unnecessary abstractions or execution frameworks. Include a small
    doctest showing the exact resulting argv. Do not execute the modeled
    command. ``CliApp.serialize`` omits values equal to declared
    defaults, even when explicitly supplied. Choose defaults with the
    executable's defaults in mind. There is no public include-defaults
    option in the verified version. A ``default_factory`` emits its
    value in that version, but this behavior is not a documented
    guarantee. Do not silently use factories to force emission.


    The pattern provides an advantage over the traditional ``extend`` by
    outsourcing to pydantic's validation and serialization.

    Examples
    --------
    >>> Ripgrep(pattern="cunt").to_argv()
    ['rg', '--regexp', 'cunt']
    >>> Ripgrep(
    ...     pattern="what's up bitches", path="src", fixed_strings=True
    ... ).to_argv()
    ['rg', '--regexp', "what's up bitches", '--fixed-strings', 'src']
    >>> Ripgrep(pattern="error", glob=["*.py", "!test_*"]).to_argv()
    ['rg', '--regexp', 'error', '--glob', '*.py', '--glob', '!test_*']

    Notes
    -----
    This pattern might not be a correct fit, but let's see if it
    survives.
    """  # noqa: DOC601, DOC603, DOC605

    model_config = SettingsConfigDict(
        use_attribute_docstrings=True,
        cli_implicit_flags=True,
        cli_kebab_case=True,
        env_prefix="RG_",
        populate_by_name=True,
        env_prefix_target="all",
    )
    """Flag serialization and environment settings."""
    pattern: str = Field(alias="regexp")
    """str: Pattern to search for, for example 'error'."""
    path: CliPositionalArg[str | None] = None
    """CliPositionalArg[str | None]: Optional file or directory to search."""
    fixed_strings: bool = False
    """bool: Treat the pattern as a literal string."""
    glob: list[str] | None = None
    """list[str] | None: File globs, for example ['*.py', '!test_*']."""
    files_with_matches: bool = False
    """bool: Print only the names of files containing matches."""
    invert_match: bool = False
    """bool: Print lines that do not match the pattern."""

    def to_argv(self) -> list[str]:
        """Return arguments for subprocess execution without a shell."""
        return ["rg", *CliApp.serialize(self, list_style="argparse")]


class Env(BaseSettings):
    """
    Environment-backed settings.

    Use BaseSettings to load environment variables that other models or
    application components need. Prefer one top-level settings model.

    Examples
    --------
    >>> from pathlib import Path
    >>> import os
    >>> from unittest.mock import patch
    >>> with patch.dict(os.environ, {"EDITOR": "nano"}):
    ...     settings = Env(
    ...         username="Hi",
    ...         shell="fish",
    ...         xdg_config_home=Path(),
    ...     )
    ...     settings.username
    'Hi'
    >>> settings.model_dump()["shell"]
    'fish'
    >>> settings.editor
    'nano'
    """  # noqa: DOC601, DOC603

    username: str
    shell: str
    editor: str = "vi"
    xdg_config_home: DirectoryPath


@validate_call
def double_count(count: PositiveInt) -> int:
    """
    Validate function arguments with ``@validate_call``.

    Parameters
    ----------
    count : PositiveInt
        A positive integer to be doubled.

    Returns
    -------
    int
        The doubled value of the input count.

    Examples
    --------
    >>> double_count(2)
    4
    >>> from pydantic import ValidationError
    >>> try:
    ...     double_count(0)
    ... except ValidationError as error:
    ...     type(error).__name__
    'ValidationError'
    """  # noqa: DOC601, DOC603

    return count * 2
