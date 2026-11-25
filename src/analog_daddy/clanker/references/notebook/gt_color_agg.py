import marimo

__generated_with = "0.25.2"
app = marimo.App(
    width="full",
    app_title="Great tables with specification based coloring.",
)

with app.setup:
    from collections.abc import Iterator

    import marimo as mo
    import polars as pl
    from great_tables import GT, loc, style, from_column
    from great_tables.data import gibraltar

    from analog_daddy.gtutils import gt_defaults
    from analog_daddy.plexpr import all_minmax_by, item_where, minmax
    from analog_daddy.plutils import metrics_to_rows
    from wigglystuff import ApiDoc


@app.cell(hide_code=True, expand_output=True)
def _(group_var, idx_var, special_case):
    mo.md(rf"""
    # Introduction

    - Goal is to have the coloring of columns controlled by a specification.
    We represent this specification as a polars expression.
    - Doing so in GT with `from_column` or `tab_style` is possible and easy. Here, I have used `tab_style`.
    - However, we need to make the coloring information survive the aggregation and it takes a bit of extra steps and that is what this notebook illustrates.
    - Additionally, doing so while maintaining your sanity, took some iterations.

    ## Terminology

    - yvars: Depedent Variables.
    - xvars: Independent Variables.

    ## What do you want to know about our data?

    1. What is the minimum and maximum value of a `yvar` across **{group_var}**?
    1. What is the value of a `yvar` at **{special_case}**?
    1. What is the value of **{idx_var}**, at the above values of `yvar`?

    ## Steps

    1. Start with your data in wide tidy format.
    1. You have to choices now. You can unpivot and fuck off. (No seriously it makes things too tough to debug when shit happens.) Jokes aside, for better or for worse, this method allows you to keep your "column name processing" within polars' logic.
    1. Alternatively, you can utilize expression expansion which means you add a new column for every computation you make. Now, there was some disappointment with the polars's handling of expression expansion, but let's reserve that for a different rant.
    1. Turn the questions we asked in the previous section into polars expression. Here, `analog_daddy.plexpr` has them.
    1. If we are aggregating, how are we dealing with any ties?
    5. Applying the correct specification (which is a polars expression). It means that the expression is evaluated for the point (row) where the minimum, maximum and the `special_case` occurs.
    6. Then reshaping the data for display and using Great tables to format it.
    """)
    return


@app.cell(hide_code=True, expand_output=True)
def _():
    mo.inspect(all_minmax_by,help=True,)
    #ApiDoc(all_minmax_by)
    #ApiDoc(item_where)
    #ApiDoc(minmax)
    # bug with broken tables in ApiDoc, hover works fine.
    return


@app.cell
def _(tbl_og_df):
    tbl_og_df
    return


@app.cell(hide_code=True)
def _():
    idx_var = "time"
    group_var = "date"
    special_case = pl.col(idx_var) == "12:20"
    yvars = ["temp", "dew_point"]
    df = (
        pl.from_pandas(gibraltar)
        .filter(
            pl.col(group_var).is_in(["2023-05-02", "2023-05-09"]),
            pl.col(idx_var).is_in(["00:20", "09:20", "12:20", "18:20"]),
        )
        .select(idx_var, group_var, *yvars)
    )
    # This GT specific syntax is added to make the table more illustrative.
    def gt_annotate(gt: GT)->GT:
        return (
            gt.tab_spanner(
            label="Y Vars.",
            columns=yvars,
        )
        .tab_spanner(
            label="Group Vars",
            columns=group_var,
        )
        .tab_spanner(
            label="Index Var.",
            columns=idx_var,
        )
        )
    tbl_og_df = (
        GT(df)
        .pipe(gt_defaults)
        .pipe(gt_annotate)
        .tab_header(title="Dummy Data")
        .tab_style(
            style=style.fill(color="lightgreen"),
            locations=loc.body(mask=special_case),
        )
    )
    return df, group_var, gt_annotate, idx_var, special_case, tbl_og_df, yvars


@app.cell
def _(df, gt_annotate):
    spec_a = pl.col("temp") > 18
    spec_b = ((pl.col("temp") - pl.col("dew_point")) < 5).alias("dew_point")
    df_with_spec = df.with_columns(
        spec_a.name.suffix("__condition"),
        spec_b.name.suffix("__condition"),
    )

    mo.output.append(
        mo.hstack(
            [
                (
                    GT(df_with_spec)
                    .pipe(gt_defaults)
                    .pipe(gt_annotate)
                    .tab_header(title="Dummy Data with Spec Evaluated")
                    .tab_spanner(
                        label="Evaluated Spec.",
                        columns=pl.col("^.*__condition$"),
                    )
                    .tab_footnote(footnote=f"spec_a = {spec_a}")
                    .tab_footnote(footnote=f"spec_b = {spec_b}")
                ),
            ],
            justify="center",
        ),
    )
    return df_with_spec, spec_a, spec_b


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Expression Expansion

    - Defining functions to generate often reused expressions as a generator.
    - Confusing part was that some polars expression don't uniformly accept expressions that expand to multiple outputs.
    - Additionally, there is no way to iterate over a polars expression (which is not a good idea usually ig), hence some helper functions resort to just accepting `list[str]`.
    """)
    return


@app.function
def spec_eval_at_minmax_y(
    y: list[str], special_case: pl.Expr
) -> Iterator[pl.Expr]:
    for i in y:
        x = pl.col(f"{i}__condition")
        minimum, maximum = all_minmax_by(x, by=[i])
        # Tied y values can have different spec results if other columns differ
        # (e.g., equal dew_point but different temp in spec_b). Here, first()
        # uses the first tied row's result, so its color depends on row order.
        # this should usually not be the case, but know that `first()` has tradeoffs.
        # a better way would be a boolean aggregation. AND/OR
        yield from (
            minimum.first().alias(f"pass_at_min__{i}"),
            item_where(x, special_case).alias(f"pass_at_special__{i}"),
            maximum.first().alias(f"pass_at_max__{i}"),
        )


@app.function
def gt_color(
    gtbl: GT,
    cols: list[str],
    from_col_id: str = "format_",
):
    """Colors a column based on a specification."""
    for col in cols:
        gtbl = gtbl.tab_style(
            style=style.fill(color=pl.col(from_col_id + col)),
            locations=loc.body(columns=pl.col(col)),
        ).cols_hide(columns=pl.col(from_col_id + col))
    return gtbl


@app.cell(hide_code=True)
def _(idx_var, special_case, yvars):
    agg_expr = [
        *minmax(pl.col(yvars)),
        *all_minmax_by(pl.col(idx_var), by=yvars),
        item_where(pl.col(yvars), special_case, prefix="special"),
        *spec_eval_at_minmax_y(y=yvars, special_case=special_case),
    ]
    agg_expr
    return (agg_expr,)


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    ## Aggregation and reshaping
    """)
    return


@app.cell
def _(agg_expr, df_with_spec, group_var, idx_var, spec_a, spec_b):
    df_aggregated = (
        df_with_spec.group_by(group_var)
        .agg(agg_expr)
        .with_columns(pl.col(pl.List).list.join(", "))
    )
    (
        GT(df_aggregated)
        .pipe(gt_defaults)
        .tab_header(title=f"Aggregated Dataframe over group {group_var}")
        .tab_spanner(
            label="Aggregate Evaluated Spec.", columns=pl.col("^pass_at_.*$")
        )
        .tab_spanner(
            label="Aggregate Y vars",
            columns=pl.col("^min__.*$", "^max__.*$", "^special__.*$"),
        )
        .tab_spanner(
            label="Condition at Y var aggregate values",
            columns=pl.col(f"^{idx_var}_at_.*$"),
        )
        .tab_spanner(label="Group Var", columns=pl.col(group_var))
        .tab_footnote(footnote=f"spec_a = {spec_a}")
        .tab_footnote(footnote=f"spec_b = {spec_b}")
    )
    return (df_aggregated,)


@app.cell
def _(df_aggregated, group_var, idx_var, spec_a, spec_b):
    (
        GT(
            df_aggregated.pipe(metrics_to_rows)
            .rename({"metric": "y_variable"})
            # needed since str doesn't autoconvert to float after pivot.
            .with_columns(pl.col("min", "max", "special").cast(pl.Float64))
        )
        .pipe(gt_defaults)
        .tab_header(title="Aggregate Dataframe after reshaping")
        .tab_spanner(
            label="Aggregate Evaluated Spec.", columns=pl.col("^pass_at_.*$")
        )
        .tab_spanner(
            label="Aggregate Y vars",
            columns=pl.col("min", "max", "special"),
        )
        .tab_spanner(
            label="Condition at Y var aggregate values",
            columns=pl.col(f"^{idx_var}_at_.*$"),
        )
        .tab_spanner(label="Group Var", columns=pl.col(group_var))
        .tab_footnote(footnote=f"spec_a = {spec_a}")
        .tab_footnote(footnote=f"spec_b = {spec_b}")
    )
    return


@app.cell
def _(df_aggregated, group_var):
    df_aggregated_colored = (
        df_aggregated.pipe(metrics_to_rows)
        .rename({"metric": "y_variable"})
        .with_columns(pl.col("min", "max", "special").cast(pl.Float64))
        .with_columns(
            pl.when(pl.col("pass_at_min") == "true")
            .then(pl.lit("lightgreen"))
            .otherwise(pl.lit("lightcoral"))
            .alias("format_min"),
            pl.when(pl.col("pass_at_special") == "true")
            .then(pl.lit("lightgreen"))
            .otherwise(pl.lit("lightcoral"))
            .alias("format_special"),
            pl.when(pl.col("pass_at_max") == "true")
            .then(pl.lit("lightgreen"))
            .otherwise(pl.lit("lightcoral"))
            .alias("format_max"),
        )
    )
    (
        GT(df_aggregated_colored)
        .pipe(gt_defaults)
        .pipe(gt_color, cols=["min", "special", "max"])
        .tab_header(
            title="Aggregate Dataframe after reshaping, colored by specification"
        )
        .tab_spanner(
            label="Aggregate Y vars", columns=pl.col("min", "max", "special")
        )
        .tab_spanner(label="Group Var", columns=pl.col(group_var))
    )
    return


if __name__ == "__main__":
    app.run()
