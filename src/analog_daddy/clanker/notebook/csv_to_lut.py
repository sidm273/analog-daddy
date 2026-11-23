import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", app_title="CSV to LUT Import")

with app.setup(hide_code=True):
    from urllib.request import urlopen

    import marimo as mo
    import polars as pl
    from xarray import Dataset, DataTree

    from analog_daddy.csv_io import UnfuckCSV
    from analog_daddy.plutils import scan_nested_params

    _dataset_url = "https://gist.githubusercontent.com/sidm273/d90f2338107821dab2e17e41f80d8527/raw/84ffe1e0e23fd13cdd68a9118eaae430e3ae0f1b/mini_GPDK45.csv"

    with urlopen(_dataset_url, timeout=30) as response:
        contents = response.read()


@app.cell
def _():
    raw_df = pl.read_csv(contents)
    indep_vars = scan_nested_params(raw_df, scan_col="Point")
    return indep_vars, raw_df


@app.cell(hide_code=True)
def _(indep_vars, raw_df):
    mo.md(f"""
    The CSV can be directly read into a dataframe. But it is untidy, and not ready for xarray.

    Independent Variables found: {indep_vars}

    {mo.as_html(raw_df)}
    """)
    return


@app.cell
def _():
    from analog_daddy.mootils import mo_table

    dataset = (
        UnfuckCSV(name="mini GPDK45", contents=contents)
        .classify()
        .read_csv()
        .tidy_df()
    )
    df = dataset.df
    mo.output.append(mo.md("## Here's a tidy version"))
    mo.output.append(mo_table(df))
    return (df,)


@app.cell(hide_code=True)
def _(df, indep_vars):
    tree: DataTree = DataTree.from_dict(
        {
            g: part.drop("group_name")
            .to_pandas()
            .set_index(indep_vars)
            .to_xarray()
            for (g,), part in df.group_by("group_name", maintain_order=True)
        }
    )
    tree
    return (tree,)


@app.cell(hide_code=True)
def _(tree: DataTree):
    nmos_svt: Dataset = tree.nmos_svt.dataset
    nmos_svt
    return


if __name__ == "__main__":
    app.run()
