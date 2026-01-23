"""Test Between."""

# standard
from datetime import datetime
from typing import TypeVar

# external
import pytest

# local
from validators import ValidationError, between

T = TypeVar("T", int, float, str, datetime)


@pytest.mark.parametrize(
    ("value", "minVal", "maxVal"),
    [(12, 11, 13), (12, None, 14), (12, 11, None), (12, 12, 12), (0, 0, 0), (0, -1, 3)],
)
def testReturnsTrueOnValidRange(value: T, minVal: T, maxVal: T):
    """Test returns true on valid range."""
    assert between(value, minVal=minVal, maxVal=maxVal)


@pytest.mark.parametrize(
    ("value", "minVal", "maxVal"),
    [
        (None, 13, 14),
        (12, 13, 14),
        (12, None, 11),
        (12, 13, None),
        (12, "13.5", datetime(1970, 1, 1)),
        ("12", 20.5, "None"),
        (datetime(1970, 1, 1), 20, "string"),
        (30, 40, "string"),
    ],
)
def testReturnsFailedValidationOnInvalidRange(value: T, minVal: T, maxVal: T):
    """Test returns failed validation on invalid range."""
    assert isinstance(between(value, minVal=minVal, maxVal=maxVal), ValidationError)
