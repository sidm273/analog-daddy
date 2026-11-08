from pydantic import BaseModel, Field

from analog_daddy.units import Length, Voltage, Width


class DefaultConfig(BaseModel):
    """
    Defaults used to describe the parameters used for sizing and sweeps.

    Examples
    --------
    >>> conf = DefaultConfig()
    >>> conf.min_length
    Length('45 nm')
    >>> conf.is_finfet
    False
    >>> conf.model_dump(context={"quantity_format": "str"})["min_width"]
    '90 nm'
    >>> conf.model_dump(context={"quantity_format": "str"})["is_finfet"]
    False
    """  # noqa: DOC601, DOC603 TODO: Use docstrings as field descriptions.

    vdd: Voltage = Field(default=Voltage("900m"), description="Supply voltage")
    is_finfet: bool = Field(
        default=False,
        description="Technology only allows integral multiples for length/width using stacking and multipliers.",
    )
    min_length: Length = Field(
        default=Length("45n"),
        description="The minimum length of your transistor",
    )
    max_length: Length = Field(
        default=Length("10 um"),
        description="The maximum length of your transistor",
    )
    length_increment: Length = Field(
        Length("10 nm"),
        description="The default increment of length (used only if is_finfet is False",
    )
    min_width: Width = Field(
        default=Width("90 nm"),
        description="The minimum width of single finger of your transistor",
    )
    max_width: Width = Field(
        default=Width("1000 um"),
        description="The maximum width of a single finger of your transistor",
    )
    voltage_step: Voltage = Field(
        default=Voltage("20 mV"),
        description="Defaults for voltage sweeps. Reducing size won't guarantee accuracy improvements beyond what was extracted.",
    )
