from __future__ import annotations

import pytest

import humanize


@pytest.mark.parametrize(
    "testArgs, expected",
    [
        ([["1", "2", "3"]], "1, 2 and 3"),
        ([["one", "two", "three"]], "one, two and three"),
        ([["one", "two"]], "one and two"),
        ([["one"]], "one"),
        ([[""]], ""),
        ([[1, 2, 3]], "1, 2 and 3"),
        ([[1, "two"]], "1 and two"),
    ],
)
def testNaturalList(
    testArgs: list[str] | list[int] | list[str | int], expected: str
) -> None:
    assert humanize.naturalList(*testArgs) == expected
