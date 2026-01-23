"""Test Card."""

# external
import pytest

# local
from validators import (
    ValidationError,
    amex,
    cardNumber,
    diners,
    discover,
    jcb,
    mastercard,
    mir,
    unionpay,
    visa,
)

visaCards = ["4242424242424242", "4000002760003184"]
mastercardCards = ["5555555555554444", "2223003122003222"]
amexCards = ["378282246310005", "371449635398431"]
unionpayCards = ["6200000000000005"]
dinersCards = ["3056930009020004", "36227206271667"]
jcbCards = ["3566002020360505"]
discoverCards = ["6011111111111117", "6011000990139424"]
mirCards = ["2200123456789019", "2204987654321098"]


@pytest.mark.parametrize(
    "value",
    visaCards
    + mastercardCards
    + amexCards
    + unionpayCards
    + dinersCards
    + jcbCards
    + discoverCards
    + mirCards,
)
def testReturnsTrueOnValidCardNumber(value: str):
    """Test returns true on valid card number."""
    assert cardNumber(value)


@pytest.mark.parametrize(
    "value",
    [
        "4242424242424240",
        "4000002760003180",
        "400000276000318X",
        "220012345678901X",
    ],
)
def testReturnsFailedOnValidCardNumber(value: str):
    """Test returns failed on valid card number."""
    assert isinstance(cardNumber(value), ValidationError)


@pytest.mark.parametrize("value", visaCards)
def testReturnsTrueOnValidVisa(value: str):
    """Test returns true on valid visa."""
    assert visa(value)


@pytest.mark.parametrize(
    "value",
    mastercardCards + amexCards + unionpayCards + dinersCards + jcbCards + discoverCards,
)
def testReturnsFailedOnValidVisa(value: str):
    """Test returns failed on valid visa."""
    assert isinstance(visa(value), ValidationError)


@pytest.mark.parametrize("value", mastercardCards)
def testReturnsTrueOnValidMastercard(value: str):
    """Test returns true on valid mastercard."""
    assert mastercard(value)


@pytest.mark.parametrize(
    "value",
    visaCards + amexCards + unionpayCards + dinersCards + jcbCards + discoverCards,
)
def testReturnsFailedOnValidMastercard(value: str):
    """Test returns failed on valid mastercard."""
    assert isinstance(mastercard(value), ValidationError)


@pytest.mark.parametrize("value", amexCards)
def testReturnsTrueOnValidAmex(value: str):
    """Test returns true on valid amex."""
    assert amex(value)


@pytest.mark.parametrize(
    "value",
    visaCards
    + mastercardCards
    + unionpayCards
    + dinersCards
    + jcbCards
    + discoverCards
    + mirCards,
)
def testReturnsFailedOnValidAmex(value: str):
    """Test returns failed on valid amex."""
    assert isinstance(amex(value), ValidationError)


@pytest.mark.parametrize("value", unionpayCards)
def testReturnsTrueOnValidUnionpay(value: str):
    """Test returns true on valid unionpay."""
    assert unionpay(value)


@pytest.mark.parametrize(
    "value",
    visaCards
    + mastercardCards
    + amexCards
    + dinersCards
    + jcbCards
    + discoverCards
    + mirCards,
)
def testReturnsFailedOnValidUnionpay(value: str):
    """Test returns failed on valid unionpay."""
    assert isinstance(unionpay(value), ValidationError)


@pytest.mark.parametrize("value", dinersCards)
def testReturnsTrueOnValidDiners(value: str):
    """Test returns true on valid diners."""
    assert diners(value)


@pytest.mark.parametrize(
    "value",
    visaCards
    + mastercardCards
    + amexCards
    + unionpayCards
    + jcbCards
    + discoverCards
    + mirCards,
)
def testReturnsFailedOnValidDiners(value: str):
    """Test returns failed on valid diners."""
    assert isinstance(diners(value), ValidationError)


@pytest.mark.parametrize("value", jcbCards)
def testReturnsTrueOnValidJcb(value: str):
    """Test returns true on valid jcb."""
    assert jcb(value)


@pytest.mark.parametrize(
    "value",
    visaCards
    + mastercardCards
    + amexCards
    + unionpayCards
    + dinersCards
    + discoverCards
    + mirCards,
)
def testReturnsFailedOnValidJcb(value: str):
    """Test returns failed on valid jcb."""
    assert isinstance(jcb(value), ValidationError)


@pytest.mark.parametrize("value", discoverCards)
def testReturnsTrueOnValidDiscover(value: str):
    """Test returns true on valid discover."""
    assert discover(value)


@pytest.mark.parametrize(
    "value",
    visaCards
    + mastercardCards
    + amexCards
    + unionpayCards
    + dinersCards
    + jcbCards
    + mirCards,
)
def testReturnsFailedOnValidDiscover(value: str):
    """Test returns failed on valid discover."""
    assert isinstance(discover(value), ValidationError)


@pytest.mark.parametrize("value", mirCards)
def testReturnsTrueOnValidMir(value: str):
    """Test returns true on valid Mir card."""
    assert mir(value)


@pytest.mark.parametrize(
    "value",
    visaCards
    + mastercardCards
    + amexCards
    + unionpayCards
    + dinersCards
    + jcbCards
    + discoverCards,
)
def testReturnsFailedOnValidMir(value: str):
    """Test returns failed on invalid Mir card (other payment systems)."""
    assert isinstance(mir(value), ValidationError)
