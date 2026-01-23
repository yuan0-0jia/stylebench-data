"""Test Indian validators."""

# external
import pytest

# local
from validators import ValidationError
from validators.i18n import indAadhar, indPan


@pytest.mark.parametrize("value", ["3675 9834 6012", "5046 3182 4299"])
def testReturnsTrueOnValidIndAadhar(value: str):
    """Test returns true on valid ind aadhar."""
    assert indAadhar(value)


@pytest.mark.parametrize("value", ["3675 9834 6012 8", "417598346012", "3675 98AF 60#2"])
def testReturnsFailedValidationOnInvalidIndAadhar(value: str):
    """Test returns failed validation on invalid ind aadhar."""
    assert isinstance(indAadhar(value), ValidationError)


@pytest.mark.parametrize("value", ["ABCDE9999K", "AAAPL1234C"])
def testReturnsTrueOnValidIndPan(value: str):
    """Test returns true on valid ind pan."""
    assert indPan(value)


@pytest.mark.parametrize("value", ["ABC5d7896B", "417598346012", "AaaPL1234C"])
def testReturnsFailedValidationOnInvalidIndPan(value: str):
    """Test returns failed validation on invalid ind pan."""
    assert isinstance(indPan(value), ValidationError)
