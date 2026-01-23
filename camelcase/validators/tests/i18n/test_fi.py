"""Test i18n/es."""

# external
import pytest

# local
from validators import ValidationError
from validators.i18n.fi import fiBusinessId, fiSsn


@pytest.mark.parametrize(
    ("value",),
    [
        ("2336509-6",),  # Supercell
        ("0112038-9",),  # Fast Monkeys
        ("2417581-7",),  # Nokia
    ],
)
def testReturnsTrueOnValidBusinessId(value: str):
    """Test returns true on valid business id."""
    assert fiBusinessId(value)


@pytest.mark.parametrize(
    ("value",),
    [
        (None,),
        ("",),
        ("1233312312",),
        ("1333333-8",),
        ("1231233-9",),
    ],
)
def testReturnsFailedValidationOnInvalidBusinessId(value: str):
    """Test returns failed validation on invalid business id."""
    assert isinstance(fiBusinessId(value), ValidationError)


@pytest.mark.parametrize(
    ("value",),
    [
        ("010190-002R",),
        ("010101-0101",),
        ("010101+0101",),
        ("010101A0101",),
        ("010190-900P",),
        ("020516C903K",),
        ("010594Y9032",),
    ],
)
def testReturnsTrueOnValidSsn(value: str):
    """Test returns true on valid ssn."""
    assert fiSsn(value)


@pytest.mark.parametrize(
    ("value",),
    [
        (None,),
        ("",),
        ("010190-001P",),  # Too low serial
        ("010190-000N",),  # Too low serial
        ("000190-0023",),  # Invalid day
        ("010090-002X",),  # Invalid month
        ("010190-002r",),  # Invalid checksum
        ("101010-0102",),
        ("10a010-0101",),
        ("101010-0\xe401",),
        ("101010b0101",),
        ("0205169C03K",),
        ("0105949Y032",),
    ],
)
def testReturnsFailedValidationOnInvalidSsn(value: str):
    """Test returns failed validation on invalid_ssn."""
    assert isinstance(fiSsn(value), ValidationError)


def testReturnsFailedValidationOnTemporalSsnWhenNotAllowed():
    """Test returns failed validation on temporal-ssn when not allowed."""
    assert isinstance(fiSsn("010190-900P", allowTemporalSsn=False), ValidationError)
