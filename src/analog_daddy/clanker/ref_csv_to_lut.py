import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")

with app.setup(hide_code=True):
    import marimo as mo
    import polars as pl
    from quantiphy import as_real
    from xarray import Dataset, DataTree

    from analog_daddy.mootils import mo_table
    from analog_daddy.plutils import (
        drop_all_null,
        explode_nested_params,
        filter_all_null,
        scan_nested_params,
    )

    _gpdk_csv_url = "https://gist.githubusercontent.com/sidm273/d90f2338107821dab2e17e41f80d8527/raw/84ffe1e0e23fd13cdd68a9118eaae430e3ae0f1b/mini_GPDK45.csv"
    raw_df = pl.read_csv(_gpdk_csv_url)


@app.cell(hide_code=True)
def _():
    mo.md(rf"""
    The CSV can be directly read into a dataframe.

    {mo.as_html(raw_df)}

    However, it isn't ready just yet to be accessible from xarray.
    """)


@app.cell(hide_code=True)
def _():
    indep_vars = scan_nested_params(raw_df, scan_col="Point")
    indep_vars
    return (indep_vars,)


@app.cell(hide_code=True)
def _(indep_vars):
    (
        exploded_df := (
            raw_df.pipe(explode_nested_params, indep_vars, index_col="Point")
            .pipe(drop_all_null)
            .select(
                pl.col("Output").alias("var_name"),
                pl.col(indep_vars),
                pl.col("Nominal").alias("var_value"),
            )
            .pipe(filter_all_null)
            .with_columns(
                pl.col(indep_vars).map_elements(
                    as_real, return_dtype=pl.Float64
                )
            )
        )
    )
    return (exploded_df,)


@app.cell(hide_code=True)
def _(exploded_df, indep_vars):
    reshaped_df = (
        exploded_df.with_columns(
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
    mo_table(reshaped_df, page_size=5)
    return (reshaped_df,)


@app.cell(hide_code=True)
def _(indep_vars, reshaped_df):
    tree: DataTree = DataTree.from_dict(
        {
            g: part.drop("group_name")
            .to_pandas()
            .set_index(indep_vars)
            .to_xarray()
            for (g,), part in reshaped_df.group_by(
                "group_name", maintain_order=True
            )
        }
    )
    tree
    return (tree,)


@app.cell(hide_code=True)
def _(tree: DataTree):
    nmos_svt: Dataset = tree.nmos_svt.dataset
    nmos_svt


if __name__ == "__main__":
    app.run()
