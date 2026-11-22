from pathlib import Path
from typing import Literal, Self

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, PositiveInt
from quantiphy import as_real

from analog_daddy.plutils import (
    drop_all_null,
    explode_nested_params,
    filter_all_null,
    scan_nested_params,
)
from analog_daddy.utils import scan_contents


class UnfuckCSV(BaseModel):
    """
    Abstraction for working with non-standard CSV files.

    Subclass this to provide your downstream code a unified
    representation of a CSV and its associated metadata.

    This abstraction restricts the horrors of reading/writing a fucked
    up CSV to this abyss of Tartarus. These motherfuckers pretend to
    follow the CSV standard and are usually observed in the corporate
    wilderness. It welcomes you with the warmth of the ",", and also
    makes you feel at home with the correct escaping of quotes. But,
    your fate was already sealed when you decided to utilize it as your
    data source. You, a novice, try to read it into a dataframe and once
    inside the dataframe, you notice that your index column is of type
    ``str``. "But it contained all numbers!" you protest. Turns out that
    same index column contained rows at regular intervals which are
    essentially nested columns.


    You try to escape and you run into your knight in shining armour
    which is the most beautiful and tidiest data of the wide format you
    have seen. Surely, this would be amenable to processing in a
    vectorized fashion, you think optimistically. But when you try
    reading it into a dataframe, your spine tingles and your brow
    sweats, when you see that the header was the second row and suddenly
    all your columns have been cast to a ``str`` type. That's when you
    know that there is no escape from the drudgery of the malformed CSV.
    Your ancestors faced it and now you face it. You wish for someone to
    have tamed this beast and scour the depths of GitHub and Stack
    Overflow to obtain the tranquilizer to put this beast to sleep.
    Unfortunately, you don't find one. Make your sacrifice count and use
    this so nothing else in your codebase suffers as badly as this part
    does.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
        use_attribute_docstrings=True,
    )
    name: str

    format_type: Literal["Detail",] | None = None
    """
    Format type of the CSV file, for classification. Add more formats as needed.
    """

    header_lineno: PositiveInt = 1
    """
    Line number of the header in the file.
    """

    n_rows: PositiveInt | None = None
    """
    Optional upper bound on number of rows to read from the CSV.
    """

    df: pl.DataFrame = Field(default_factory=pl.DataFrame)

    contents: bytes | Path
    """
    Actual contents of the CSV file.
    """

    def classify(self) -> Self:
        """
        Classify CSV file with a quick peek of the contents.

        Logic to classify the CSV file into one of the
        :attr:`format_type`. Usually, this can be done without reading
        the file as a dataframe and rather by checking for patterns.
        """
        # Search for specific patterns.
        header_pattern = "^Point,"
        try:
            self.header_lineno = next(
                scan_contents(
                    contents=self.contents,
                    search_pattern=header_pattern,
                )
            )
        except StopIteration as e:
            err_msg = f"Pattern {header_pattern} not found in {self.name}"
            raise ValueError(err_msg) from e

        parameter_pattern = '^"Parameters: '
        parameters = scan_contents(
            contents=self.contents,
            search_pattern=parameter_pattern,
        )
        try:
            # classify based on location of patterns.
            if self.header_lineno == next(parameters) - 1:
                self.format_type = "Detail"
            else:
                err_msg = "Unsupported format."
                raise ValueError(err_msg)
        except StopIteration as e:
            err_msg = f"Pattern {parameter_pattern} not found in {self.name}"
            raise ValueError(err_msg) from e

        return self

    def read_csv(
        self,
        null_values: tuple[str, ...] = (
            "nil",
            "eval error",
            "eval err",
            "canceled",
            "pending",
            "-",
            "",
        ),
    ) -> Self:
        """
        Read the classified CSV file into a polars DataFrame.

        Logic to read the classified file into the dataframe. It might
        not guarantee that the dataframe is tidy, since doing that might
        require some dataframe level processing.
        """
        if self.format_type == "Detail":
            pass
        else:
            err_msg = f"Unsupported format_type: {self.format_type}"
            raise ValueError(err_msg)

        self.df = pl.read_csv(
            source=self.contents,
            has_header=True,
            skip_lines=self.header_lineno - 1,
            n_rows=self.n_rows,
            null_values=null_values,
        )
        return self

    def tidy_df(
        self,
    ) -> Self:
        """
        Logic to tidy up the dataframe.
        """
        if self.format_type == "Detail":
            self.df_detail_tidy(
                index_col="Point",
                var_name="Output",
                var_value="Nominal",
            )
        else:
            err_msg = f"Unsupported format_type: {self.format_type}"
            raise ValueError(err_msg)

        return self

    def df_detail_tidy(
        self,
        index_col="Point",
        var_name="Output",
        var_value="Nominal",
    ) -> Self:
        """
        An example to tidy a Dataframe containing nested rows.
        """
        indep_vars = scan_nested_params(self.df, scan_col=index_col)

        self.df = (
            self.df.pipe(
                explode_nested_params,
                indep_vars,
                index_col=index_col,
            )
            # cleanup.
            .pipe(drop_all_null)
            .select(
                pl.col(var_name).alias("var_name"),
                pl.col(indep_vars),
                pl.col(var_value).alias("var_value"),
            )
            .pipe(filter_all_null)
            # cast SI prefixed numbers.
            .with_columns(
                pl.col(indep_vars).map_elements(
                    as_real,
                    return_dtype=pl.Float64,
                )
            )
            # reshaping
            .with_columns(
                pl.col("var_name")
                .str.splitn("_", n=2)
                .struct.rename_fields(["var_name", "group_name"])
            )
            .unnest()
            .pivot(
                on="var_name",
                index=["group_name", *indep_vars],
                values="var_value",
            )
        )
        return self
