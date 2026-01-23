"""Validate Anything!"""

# local
from .between import between
from .card import amex, cardNumber, diners, discover, jcb, mastercard, mir, unionpay, visa
from .country import callingCode, countryCode, currency
from .cron import cron
from .crypto_addresses import bscAddress, btcAddress, ethAddress, trxAddress
from .domain import domain
from .email import email
from .encoding import base16, base32, base58, base64
from .finance import cusip, isin, sedol
from .hashes import md5, sha1, sha224, sha256, sha384, sha512
from .hostname import hostname
from .i18n import (
    esCif,
    esDoi,
    esNie,
    esNif,
    fiBusinessId,
    fiSsn,
    frDepartment,
    frSsn,
    indAadhar,
    indPan,
    ruInn,
)
from .iban import iban
from .ip_address import ipv4, ipv6
from .length import length
from .mac_address import macAddress
from .slug import slug
from .url import url
from .utils import ValidationError, validator
from .uuid import uuid

__all__ = (
    # ...
    "between",
    # crypto_addresses
    "bscAddress",
    "btcAddress",
    "ethAddress",
    "trxAddress",
    # cards
    "amex",
    "cardNumber",
    "diners",
    "discover",
    "jcb",
    "mastercard",
    "unionpay",
    "visa",
    "mir",
    # country
    "callingCode",
    "countryCode",
    "currency",
    # ...
    "cron",
    # ...
    "domain",
    # ...
    "email",
    # encodings
    "base16",
    "base32",
    "base58",
    "base64",
    # finance
    "cusip",
    "isin",
    "sedol",
    # hashes
    "md5",
    "sha1",
    "sha224",
    "sha256",
    "sha384",
    "sha512",
    # ...
    "hostname",
    # i18n
    "esCif",
    "esDoi",
    "esNie",
    "esNif",
    "fiBusinessId",
    "fiSsn",
    "frDepartment",
    "frSsn",
    "indAadhar",
    "indPan",
    "ruInn",
    # ...
    "iban",
    # ip_addresses
    "ipv4",
    "ipv6",
    # ...
    "length",
    # ...
    "macAddress",
    # ...
    "slug",
    # ...
    "url",
    # ...
    "uuid",
    # utils
    "ValidationError",
    "validator",
)

__version__ = "0.35.0"
