"""Test IBAN."""

# external
import pytest

# local
from validators import ValidationError, iban


@pytest.mark.parametrize("value", ["GB82WEST12345698765432", "NO9386011117947"])
def testReturnsTrueOnValidIban(value: str):
    """Test returns true on valid iban."""
    assert iban(value)


@pytest.mark.parametrize("value", ["GB81WEST12345698765432", "NO9186011117947"])
def testReturnsFailedValidationOnInvalidIban(value: str):
    """Test returns failed validation on invalid iban."""
    assert isinstance(iban(value), ValidationError)
