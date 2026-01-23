"""Test Length."""

# external
import pytest

# local
from validators import ValidationError, length


@pytest.mark.parametrize(
    ("value", "minVal", "maxVal"),
    [("password", 2, None), ("password", None, None), ("password", 0, 10), ("password", 8, 8)],
)
def testReturnsTrueOnValidLength(value: str, minVal: int, maxVal: int):
    """Test returns true on valid length."""
    assert length(value, minVal=minVal, maxVal=maxVal)


@pytest.mark.parametrize(
    ("value", "minVal", "maxVal"),
    [("something", 14, 12), ("something", -10, -20), ("something", 0, -2), ("something", 13, 14)],
)
def testReturnsFailedValidationOnInvalidRange(value: str, minVal: int, maxVal: int):
    """Test returns failed validation on invalid range."""
    assert isinstance(length(value, minVal=minVal, maxVal=maxVal), ValidationError)
