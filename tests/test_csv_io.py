################
# Created/Changed using: Crush/gpt-6.1-sol
# HUMAN VERIFICATION: Meh, looks okay.
################
"""Regression and property-based tests using the GPDK45 CSV fixture."""

import csv
from pathlib import Path

import polars as pl
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from polars.testing import assert_frame_equal
from pydantic import ValidationError

from analog_daddy.csv_io import UnfuckCSV

_DATA_PATH = Path(__file__).parent / "data" / "GPDK45.csv"
_CONTENTS = _DATA_PATH.read_bytes()
_HEADER = _CONTENTS.splitlines()[0] + b"\n"
_BLOCKS = tuple(
    b'"Parameters: ' + block for block in _CONTENTS.split(b'"Parameters: ')[1:]
)
_PREAMBLE = st.lists(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789 ,", min_size=1),
    max_size=5,
).map(lambda lines: "".join(f"{line}\n" for line in lines).encode())
_NULL_VALUES = (
    "nil",
    "eval error",
    "eval err",
    "canceled",
    "pending",
    "-",
    "",
)


def _parameter_value(value: str) -> float:
    return (
        float(value[:-1]) * {"m": 1e-3, "u": 1e-6}[value[-1]]
        if value[-1] in "mu"
        else float(value)
    )


def _expected_block(block: bytes) -> list[dict[str, str | float]]:
    rows = csv.reader(block.decode().splitlines())
    parameters = {
        key: _parameter_value(value)
        for key, value in (
            pair.split("=")
            for pair in next(rows)[0].removeprefix("Parameters: ").split(", ")
        )
    }
    groups: dict[str, dict[str, str | float]] = {}
    for row in rows:
        metric, group = row[2].split("_", 1)
        record = groups.setdefault(group, {"group_name": group, **parameters})
        record[metric] = float(row[3])
    return list(groups.values())


@pytest.mark.parametrize("source_type", ["path", "bytes"])
def test_gpdk_full_pipeline(source_type: str) -> None:
    contents = _DATA_PATH if source_type == "path" else _CONTENTS
    dataset = UnfuckCSV(name="GPDK45", contents=contents)

    assert dataset.classify() is dataset
    assert dataset.format_type == "Detail"
    assert dataset.header_lineno == 1
    assert dataset.read_csv() is dataset
    assert dataset.df.shape == (2736, 7)
    assert dataset.tidy_df() is dataset

    expected = pl.DataFrame(
        [row for block in _BLOCKS for row in _expected_block(block)]
    )
    assert dataset.df.shape == (288, 14)
    assert_frame_equal(dataset.df, expected, check_row_order=False)


@settings(max_examples=30, deadline=None)
@given(
    indices=st.lists(
        st.integers(min_value=0, max_value=len(_BLOCKS) - 1),
        min_size=1,
        max_size=8,
        unique=True,
    ),
    preamble=_PREAMBLE,
    newline=st.sampled_from([b"\n", b"\r\n"]),
)
def test_gpdk_blocks_preserve_values_and_parameters(
    indices: list[int], preamble: bytes, newline: bytes
) -> None:
    blocks = [_BLOCKS[index] for index in indices]
    contents = (preamble + _HEADER + b"".join(blocks)).replace(b"\n", newline)
    dataset = UnfuckCSV(name="GPDK45 subset", contents=contents)

    assert dataset.classify().read_csv().tidy_df() is dataset
    assert dataset.header_lineno == preamble.count(b"\n") + 1
    expected = pl.DataFrame(
        [row for block in blocks for row in _expected_block(block)]
    )
    assert_frame_equal(dataset.df, expected, check_row_order=False)


@given(n_rows=st.integers(min_value=1, max_value=2736))
def test_gpdk_read_respects_row_limit(n_rows: int) -> None:
    dataset = UnfuckCSV(name="GPDK45", contents=_CONTENTS, n_rows=n_rows)
    dataset.classify().read_csv()

    assert dataset.df.height == n_rows


@given(preamble=_PREAMBLE)
def test_missing_header_raises_value_error(preamble: bytes) -> None:
    dataset = UnfuckCSV(name="missing header", contents=preamble + _BLOCKS[0])

    with pytest.raises(ValueError) as exc_info:
        dataset.classify()

    assert str(exc_info.value) == "Pattern ^Point, not found in missing header"
    assert isinstance(exc_info.value.__cause__, StopIteration)


@given(preamble=_PREAMBLE)
def test_missing_parameters_raises_value_error(preamble: bytes) -> None:
    measurements = _BLOCKS[0].split(b"\n", 1)[1]
    dataset = UnfuckCSV(
        name="missing parameters", contents=preamble + _HEADER + measurements
    )

    with pytest.raises(ValueError) as exc_info:
        dataset.classify()

    assert str(exc_info.value) == (
        'Pattern ^"Parameters:  not found in missing parameters'
    )
    assert isinstance(exc_info.value.__cause__, StopIteration)


@given(preamble=_PREAMBLE, gap=st.integers(min_value=1, max_value=5))
def test_nonadjacent_parameters_are_unsupported(
    preamble: bytes, gap: int
) -> None:
    dataset = UnfuckCSV(
        name="unsupported layout",
        contents=preamble + _HEADER + b"metadata\n" * gap + _BLOCKS[0],
    )

    with pytest.raises(ValueError) as exc_info:
        dataset.classify()

    assert str(exc_info.value) == "Unsupported format."


@pytest.mark.parametrize("method", ["read_csv", "tidy_df"])
def test_unclassified_csv_is_rejected(method: str) -> None:
    dataset = UnfuckCSV(name="GPDK45", contents=_CONTENTS)

    with pytest.raises(ValueError, match="Unsupported format_type: None"):
        getattr(dataset, method)()


@given(null_value=st.sampled_from(_NULL_VALUES))
def test_read_normalizes_default_null_values(null_value: str) -> None:
    contents = _HEADER + _BLOCKS[0].replace(
        b"53.26e-15", null_value.encode(), 1
    )
    dataset = UnfuckCSV(name="null marker", contents=contents)
    dataset.classify().read_csv()

    assert dataset.df["Nominal"][1] is None
    assert dataset.df["Nominal"][2] == pytest.approx(3.685e-15)


def test_read_accepts_custom_null_values() -> None:
    contents = _HEADER + _BLOCKS[0].replace(b"53.26e-15", b"missing", 1)
    dataset = UnfuckCSV(name="custom null marker", contents=contents)
    dataset.classify().read_csv(null_values=("missing",))

    assert dataset.df["Nominal"][1] is None


def test_detail_tidy_accepts_custom_column_names() -> None:
    dataset = UnfuckCSV(name="renamed columns", contents=_HEADER + _BLOCKS[0])
    dataset.classify().read_csv()
    dataset.df = dataset.df.rename(
        {"Point": "index", "Output": "metric", "Nominal": "value"}
    )

    assert (
        dataset.df_detail_tidy(
            index_col="index", var_name="metric", var_value="value"
        )
        is dataset
    )
    assert_frame_equal(dataset.df, pl.DataFrame(_expected_block(_BLOCKS[0])))


@pytest.mark.parametrize("field", ["header_lineno", "n_rows"])
@given(value=st.integers(max_value=0))
def test_nonpositive_row_settings_are_rejected(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        UnfuckCSV.model_validate(
            {"name": "invalid rows", "contents": _CONTENTS, field: value}
        )


def test_default_dataframes_are_independent() -> None:
    first = UnfuckCSV(name="first", contents=_CONTENTS)
    second = UnfuckCSV(name="second", contents=_CONTENTS)

    assert first.df is not second.df
    first.classify().read_csv()
    assert second.df.is_empty()
