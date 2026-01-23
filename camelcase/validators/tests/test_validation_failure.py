"""Test validation Failure."""

# local
from validators import between

failedObjRepr = "ValidationError(func=between"


class TestValidationError:
    """Test validation Failure."""

    def setup_method(self):
        """Setup Method."""
        self.isInBetween = between(3, minVal=4, maxVal=5)

    def testBooleanCoerce(self):
        """Test Boolean."""
        assert not bool(self.isInBetween)
        assert not self.isInBetween

    def testRepr(self):
        """Test Repr."""
        assert failedObjRepr in repr(self.isInBetween)

    def testString(self):
        """Test Repr."""
        assert failedObjRepr in str(self.isInBetween)

    def testArgumentsAsProperties(self):
        """Test argument properties."""
        assert self.isInBetween.__dict__["value"] == 3
        assert self.isInBetween.__dict__["minVal"] == 4
        assert self.isInBetween.__dict__["maxVal"] == 5
