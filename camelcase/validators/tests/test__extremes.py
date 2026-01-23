"""Test Extremes."""

# standard
from typing import Any

# external
import pytest

# local
from validators._extremes import AbsMax, AbsMin

absMax = AbsMax()
absMin = AbsMin()


@pytest.mark.parametrize(
    ("value",),
    [(None,), ("",), (12,), (absMin,)],
)
def testAbsMaxIsGreaterThanEveryOtherValue(value: Any):
    """Test if AbsMax is greater than every other value."""
    assert value < absMax
    assert absMax > value


def testAbsMaxIsNotGreaterThanItself():
    """Test if AbsMax is not greater than itself."""
    assert not (absMax > absMax)


def testOtherComparisonMethodsForAbsMax():
    """Test other comparison methods for AbsMax."""
    assert absMax <= absMax
    assert absMax == absMax
    assert absMax == absMax


@pytest.mark.parametrize(
    ("value",),
    [(None,), ("",), (12,), (absMax,)],
)
def testAbsMinIsSmallerThanEveryOtherValue(value: Any):
    """Test if AbsMin is less than every other value."""
    assert value > absMin


def testAbsMinIsNotGreaterThanItself():
    """Test if AbsMin is not less than itself."""
    assert not (absMin < absMin)


def testOtherComparisonMethodsForAbsMin():
    """Test other comparison methods for AbsMin."""
    assert absMin <= absMin
    assert absMin == absMin
    assert absMin == absMin
