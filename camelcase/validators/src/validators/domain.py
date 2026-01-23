"""Domain."""

# standard
from os import environ
from pathlib import Path
import re
from typing import Optional, Set

# local
from .utils import validator


class _ianatld:
    """Read IANA TLDs, and optionally cache them."""

    _fullCache: Optional[Set[str]] = None
    # source: https://www.statista.com/statistics/265677
    _popularCache = {"COM", "ORG", "RU", "DE", "NET", "BR", "UK", "JP", "FR", "IT"}
    _popularCache.add("ONION")

    @classmethod
    def _retrieve(cls):
        with Path(__file__).parent.joinpath("_tld.txt").open() as tldF:
            _ = next(tldF)  # ignore the first line
            for line in tldF:
                yield line.strip()

    @classmethod
    def check(cls, tld: str):
        if tld in cls._popularCache:
            return True
        if cls._fullCache is None:
            if environ.get("PYVLD_CACHE_TLD") == "True":
                cls._fullCache = set(cls._retrieve())
            else:
                return tld in cls._retrieve()
        return tld in cls._fullCache


@validator
def domain(
    value: str, /, *, considerTld: bool = False, rfc1034: bool = False, rfc2782: bool = False
):
    """Return whether or not given value is a valid domain.

    Examples:
        >>> domain('example.com')
        True
        >>> domain('example.com/')
        ValidationError(func=domain, args={'value': 'example.com/'})
        >>> # Supports IDN domains as well::
        >>> domain('xn----gtbspbbmkef.xn--p1ai')
        True

    Args:
        value:
            Domain string to validate.
        consider_tld:
            Restrict domain to TLDs allowed by IANA.
        rfc_1034:
            Allows optional trailing dot in the domain name.
            Ref: [RFC 1034](https://www.rfc-editor.org/rfc/rfc1034).
        rfc_2782:
            Domain name is of type service record.
            Allows optional underscores in the domain name.
            Ref: [RFC 2782](https://www.rfc-editor.org/rfc/rfc2782).


    Returns:
        (Literal[True]): If `value` is a valid domain name.
        (ValidationError): If `value` is an invalid domain name.

    Raises:
        (UnicodeError): If `value` cannot be encoded into `idna` or decoded into `utf-8`.
    """
    if not value:
        return False

    if considerTld and not _ianatld.check(value.rstrip(".").rsplit(".", 1)[-1].upper()):
        return False

    try:
        serviceRecord = r"_" if rfc2782 else ""
        trailingDot = r"\.?$" if rfc1034 else r"$"

        return not re.search(r"\s|__+", value) and re.match(
            # First character of the domain
            rf"^(?:[a-z0-9{serviceRecord}]"
            # Sub-domain
            + rf"(?:[a-z0-9-{serviceRecord}]{{0,61}}"
            # Hostname
            + rf"[a-z0-9{serviceRecord}])?\.)"
            # First 61 characters of the gTLD
            + r"+[a-z0-9][a-z0-9-_]{0,61}"
            # Last character of the gTLD
            + rf"[a-z]{trailingDot}",
            value.encode("idna").decode("utf-8"),
            re.IGNORECASE,
        )
    except UnicodeError as err:
        raise UnicodeError(f"Unable to encode/decode {value}") from err
