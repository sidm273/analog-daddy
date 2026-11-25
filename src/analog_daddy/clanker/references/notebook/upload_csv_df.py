import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", app_title="Upload file")


@app.cell
def _():
    import marimo as mo
    from quantiphy import as_real

    return as_real, mo


@app.cell(hide_code=True)
def _(as_real, mo):
    uploads = mo.ui.file(
        filetypes=[".csv", ".tsv"],
        kind="area",
        max_size=int(as_real("50 MB")),
        multiple=False,
        label="Upload CSV/TSV files here!",
    )
    return (uploads,)


@app.cell(hide_code=True)
def _(mo, uploads):
    mo.md(rf"""
    {uploads}
    {
        mo.stop(
            not uploads.value,
            mo.callout("Upload the files to continue", kind="danger"),
        )
    }
    """)
    return


@app.cell(hide_code=True)
def _(mo, uploads):
    mo.md(rf"""
    {uploads}
    """)
    return


if __name__ == "__main__":
    app.run()
