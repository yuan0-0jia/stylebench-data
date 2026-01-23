"""Test BTC address."""

# external
import pytest

# local
from validators import ValidationError, btcAddress


@pytest.mark.parametrize(
    "value",
    [
        # P2PKH (Pay-to-PubkeyHash) type
        "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2",
        # P2SH (Pay to script hash) type
        "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy",
        # Bech32/segwit type
        "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",
        "bc1qc7slrfxkknqcq2jevvvkdgvrt8080852dfjewde450xdlk4ugp7szw5tk9",
    ],
)
def testReturnsTrueOnValidBtcAddress(value: str):
    """Test returns true on valid btc address."""
    assert btcAddress(value)


@pytest.mark.parametrize(
    "value",
    [
        "ff3Cwgr2g7vsi1bXDUkpEnVoRLA9w4FZfC69",
        "b3Cgwgr2g7vsi1bXyjyDUkphEnVoRLA9w4FZfC69",
        # incorrect header
        "1BvBMsEYstWetqTFn5Au4m4GFg7xJaNVN2",
        # incorrect checksum
        "3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLz",
    ],
)
def testReturnsFailedValidationOnInvalidBtcAddress(value: str):
    """Test returns failed validation on invalid btc address."""
    assert isinstance(btcAddress(value), ValidationError)
