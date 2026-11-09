"""
Reference model of preferred Pydantic programming pattern.

Before creating new pydantic models, reuse the fields, validators,
config patterns and types defined here. Only introduce new Pydantic
features after exhausting what's available in this file and after
consulting the user.
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
from pydantic_settings import BaseSettings

from analog_daddy.units import Time

Extensions = Literal["zip", "tar.gz", "7z"]


class KitchenSink(BaseModel):
    """
    A reference model containing most used patterns.

    Key features include, customized serialization aliases, using custom
    types and its serialization preferences. Field descriptions serve as
    usage examples. Keep new field descriptions equally explicit.

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
        alias_generator=AliasGenerator(
            serialization_alias=to_camel,
        ),
    )
    base_command: str
    sub_command: tuple[str, ...] = ("release", "download")
    middle_name: str = Field(
        default="Reginald",
        description="Middle name of the person.",
    )
    created_at: float = Field(default_factory=time.time)
    directory: DirectoryPath
    archive: Literal["zip", "tar.gz"] = "zip"
    acceptable_ext: list[Extensions] = Field(
        default=["zip"],
        description="A list of acceptable extensions.",
    )
    start_time: Time = Time("1n")
    log_path: FilePath | None = None
    n: PositiveInt = Field(default=2)
    age: int = Field(ge=0, le=150, description="User age", default=30)
    custom_logpath: NewPath | Literal["%J.out"] = Field(
        default="%J.out",
        description="A custom new path field.",
    )
    listicle: list[tuple[str, int | str]] = Field(
        default=[("item1", 1), ("item2", "2n")]
    )


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
