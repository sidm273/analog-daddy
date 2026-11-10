"""Currently not stable and functional."""

from typing import Literal

from xarray import DataArray, Dataset


def look_up(
    *,  # force kwargs
    data: Dataset,
    outvar: str,
    length: DataArray | None = None,
    vgs: DataArray | None = None,
    vds: DataArray | None = None,
    vsb: DataArray | None = None,
    ratio_seperator: tuple[str, str] = ("_", "/"),
    **kwargs,
) -> DataArray:
    # Making the outvar lowercase to avoid case sensitivity
    outvar = outvar.lower()
    mode: Literal["no_ratio", "outvar_ratio", "both_ratios"]

    interp_defaults = {
        "ds": data.ds.max().item() / 2,
        "length": data.length.min().item(),
        "gs": data.gs,
        "sb": data.sb.min().item(),
    }

    if any(sep in outvar for sep in ratio_seperator):
        mode = "outvar_ratio"
        ydata = split_var(data, outvar, ratio_seperator)
    else:
        mode = "no_ratio"
        ydata = data[outvar]

    # Data extraction and interpolation for mode 1 and mode 2
    if mode == "outvar_ratio" and any("_" in key for key in kwargs):
        mode = "both_ratios"
        msg = f"Mode:{mode}. Interpolation for both ratios is not implemented yet."
        raise NotImplementedError(msg)

    _ = (
        length,
        vgs,
        vds,
        vsb,
        mode,
    )
    return ydata.interp(coords=interp_defaults)


def split_var(
    data: Dataset,
    var_name: str,
    _ratio_seperator: tuple[str, str] = ("_", "/"),
) -> DataArray:
    """
    Splits a variable name into its numerator and denominator components
    if it is a ratio.
    """
    numerator, denominator = var_name.split("_")
    return data[numerator] / data[denominator]
