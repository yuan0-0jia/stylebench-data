"""Test Country."""

# external
import pytest

# local
from validators import ValidationError, callingCode, countryCode, currency


@pytest.mark.parametrize(("value"), ["+1", "+371"])
def testReturnsTrueOnValidCallingCode(value: str):
    """Test returns true on valid calling code."""
    assert callingCode(value)


@pytest.mark.parametrize(("value"), ["+19", "+37", "-9"])
def testReturnsFailedValidationInvalidCallingCode(value: str):
    """Test returns failed validation invalid calling code."""
    assert isinstance(callingCode(value), ValidationError)


@pytest.mark.parametrize(
    ("value", "isoFormat"),
    [
        ("ISR", "auto"),
        ("US", "alpha2"),
        ("USA", "alpha3"),
        ("840", "numeric"),
    ],
)
def testReturnsTrueOnValidCountryCode(value: str, isoFormat: str):
    """Test returns true on valid country code."""
    assert countryCode(value, isoFormat=isoFormat)


@pytest.mark.parametrize(
    ("value", "isoFormat"),
    [
        (None, "auto"),
        ("", "auto"),
        ("123456", "auto"),
        ("XY", "alpha2"),
        ("PPP", "alpha3"),
        ("123", "numeric"),
        ("us", "auto"),
        ("uSa", "auto"),
        ("US ", "auto"),
        ("U.S", "auto"),
        ("1ND", "unknown"),
        ("ISR", None),
    ],
)
def testReturnsFailedValidationOnInvalidCountryCode(value: str, isoFormat: str):
    """Test returns failed validation on invalid country code."""
    assert isinstance(countryCode(value, isoFormat=isoFormat), ValidationError)


@pytest.mark.parametrize(
    ("value", "skipSymbols", "ignoreCase"), [("$", False, False), ("uSd", True, True)]
)
def testReturnsTrueOnValidCurrency(value: str, skipSymbols: bool, ignoreCase: bool):
    """Test returns true on valid currency."""
    assert currency(value, skipSymbols=skipSymbols, ignoreCase=ignoreCase)


@pytest.mark.parametrize(
    ("value", "skipSymbols", "ignoreCase"),
    [("$", True, False), ("uSd", True, False), ("Bucks", True, True)],
)
def testReturnsFailedValidationInvalidCurrency(
    value: str, skipSymbols: bool, ignoreCase: bool
):
    """Test returns failed validation invalid currency."""
    assert isinstance(
        currency(value, skipSymbols=skipSymbols, ignoreCase=ignoreCase), ValidationError
    )
