import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full")


@app.cell
def _():
    import polars as pl
    import polars.selectors as cs
    from great_tables import GT
    from great_tables.data import gtcars as dataset

    from analog_daddy.plexpr import list_cast, list_render_unique

    return GT, cs, dataset, list_cast, list_render_unique, pl


@app.cell
def _(dataset, pl):
    df = pl.from_pandas(dataset)
    df
    return (df,)


@app.cell(expand_output=True)
def _(GT, cs, df, list_cast, list_render_unique, pl):
    GT(
        df.select("mfr", "model", "bdy_style", "drivetrain", "ctry_origin")
        .group_by(pl.col("ctry_origin"))
        .agg(
            cs.numeric(),
            cs.string(),
        )
        .with_columns(cs.list().list.unique())
        .with_columns(list_cast())
        .with_columns(list_render_unique())
    )
    return


if __name__ == "__main__":
    app.run()
