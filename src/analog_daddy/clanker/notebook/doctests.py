import marimo

__generated_with = "0.25.2"
app = marimo.App(width="full", app_title="Doctests in marimo")

with app.setup(hide_code=True):
    from analog_daddy.mootils import rich_md
    import marimo as mo


@app.cell(hide_code=True)
def _():
    mo.md(r"""
    # Doctests
    """)
    return


@app.function
def mult_2(a: int) -> int:
    """
    Multiply a number by two.

    Parameters
    ----------
    a : int
        The number to multiply.

    Returns
    -------
    int
        The input multiplied by two.

    Examples
    --------
    >>> mult_2(1)
    2
    >>> mult_2(0)
    0
    """
    return a * 2


@app.cell(hide_code=True)
def _():
    import doctest
    # testmod uses anything within the current module.
    # `function_list` is added so that if any of the function changes
    # the doctests are autorun by marimo.
    failures, success = doctest.testmod(report=True,verbose=True,exclude_empty=True)
    _x = rich_md(f"[bold green]Success: {success}[/]")
    _y = rich_md(f"[bold red]Failures: {failures}[/]")
    _function_list = (mult_2,)

    _acc = mo.md(f"""## Doctest Results
    - {_x}
    - {_y}

    /// details | Expand for function lists.
    Here we are creating a tuple of all the reusable functions to explicitly force the current marimo cell to be a dependency of the function cells to trigger an autorun on change. This is a hack.

    {
        mo.accordion(
            {val.__name__: mo.inspect(val, help=False) for val in _function_list},
            multiple=True,
        )
    }
    ///
    """)
    mo.output.append(_acc)
    return


if __name__ == "__main__":
    app.run()
