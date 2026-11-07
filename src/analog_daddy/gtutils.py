import polars.selectors as cs
from great_tables import GT

__all__ = ["gt_defaults"]


def gt_defaults(gtbl: GT):
    """Preferred defaults for rendering great tables."""
    return gtbl.fmt_number_si(columns=cs.numeric()).opt_stylize(style=4)
