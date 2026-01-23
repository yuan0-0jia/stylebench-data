"""Crypto addresses."""

# local
from .bsc_address import bscAddress
from .btc_address import btcAddress
from .eth_address import ethAddress
from .trx_address import trxAddress

__all__ = ("bscAddress", "btcAddress", "ethAddress", "trxAddress")
