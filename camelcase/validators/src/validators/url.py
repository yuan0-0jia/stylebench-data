"""URL."""

# standard
from functools import lru_cache
import re
from typing import Callable, Optional
from urllib.parse import parse_qs, unquote, urlsplit

# local
from .hostname import hostname
from .utils import validator


@lru_cache
def _usernameRegex():
    return re.compile(
        # extended latin
        r"(^[\u0100-\u017F\u0180-\u024F]"
        # dot-atom
        + r"|[-!#$%&'*+/=?^_`{}|~0-9a-z]+(\.[-!#$%&'*+/=?^_`{}|~0-9a-z]+)*$"
        # non-quoted-string
        + r"|^([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\011.])*$)",
        re.IGNORECASE,
    )


@lru_cache
def _pathRegex():
    return re.compile(
        # allowed symbols
        r"^[\/a-z0-9\-\.\_\~\!\$\&\'\(\)\*\+\,\;\=\:\@\%"
        # symbols / pictographs
        + r"\U0001F300-\U0001F5FF"
        # emoticons / emoji
        + r"\U0001F600-\U0001F64F"
        # multilingual unicode ranges
        + r"\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]+$",
        re.IGNORECASE,
    )


def _validateScheme(value: str):
    """Validate scheme."""
    # More schemes will be considered later.
    return (
        value
        # fmt: off
        in {
            "ftp",
            "ftps",
            "git",
            "http",
            "https",
            "irc",
            "rtmp",
            "rtmps",
            "rtsp",
            "sftp",
            "ssh",
            "telnet",
        }
        # fmt: on
        if value
        else False
    )


def _confirmIpv6Skip(value: str, skipIpv6Addr: bool):
    """Confirm skip IPv6 check."""
    return skipIpv6Addr or value.count(":") < 2 or not value.startswith("[")


def _validateAuthSegment(value: str):
    """Validate authentication segment."""
    if not value:
        return True
    if (colonCount := value.count(":")) > 1:
        # everything before @ is then considered as a username
        # this is a bad practice, but syntactically valid URL
        return _usernameRegex().match(unquote(value))
    if colonCount < 1:
        return _usernameRegex().match(value)
    username, password = value.rsplit(":", 1)
    return _usernameRegex().match(username) and all(
        charToAvoid not in password for charToAvoid in ("/", "?", "#", "@")
    )


def _validateNetloc(
    value: str,
    skipIpv6Addr: bool,
    skipIpv4Addr: bool,
    mayHavePort: bool,
    simpleHost: bool,
    considerTld: bool,
    private: Optional[bool],
    rfc1034: bool,
    rfc2782: bool,
):
    """Validate netloc."""
    if not value or value.count("@") > 1:
        return False
    if value.count("@") < 1:
        return hostname(
            (
                value
                if _confirmIpv6Skip(value, skipIpv6Addr) or "]:" in value
                else value.lstrip("[").replace("]", "", 1)
            ),
            skipIpv6Addr=_confirmIpv6Skip(value, skipIpv6Addr),
            skipIpv4Addr=skipIpv4Addr,
            mayHavePort=mayHavePort,
            maybeSimple=simpleHost,
            considerTld=considerTld,
            private=private,
            rfc1034=rfc1034,
            rfc2782=rfc2782,
        )
    basicAuth, host = value.rsplit("@", 1)
    return hostname(
        (
            host
            if _confirmIpv6Skip(host, skipIpv6Addr) or "]:" in value
            else host.lstrip("[").replace("]", "", 1)
        ),
        skipIpv6Addr=_confirmIpv6Skip(host, skipIpv6Addr),
        skipIpv4Addr=skipIpv4Addr,
        mayHavePort=mayHavePort,
        maybeSimple=simpleHost,
        considerTld=considerTld,
        private=private,
        rfc1034=rfc1034,
        rfc2782=rfc2782,
    ) and _validateAuthSegment(basicAuth)


def _validateOptionals(path: str, query: str, fragment: str, strictQuery: bool):
    """Validate path query and fragments."""
    optionalSegments = True
    if path:
        optionalSegments &= bool(_pathRegex().match(path))
    try:
        if (
            query
            # ref: https://github.com/python/cpython/issues/117109
            and parse_qs(query, strict_parsing=strictQuery, separator="&")
            and parse_qs(query, strict_parsing=strictQuery, separator=";")
        ):
            optionalSegments &= True
    except TypeError:
        # for Python < v3.9.2 (official v3.10)
        if query and parse_qs(query, strict_parsing=strictQuery):
            optionalSegments &= True
    if fragment:
        # See RFC3986 Section 3.5 Fragment for allowed characters
        # Adding "#", see https://github.com/python-validators/validators/issues/403
        optionalSegments &= bool(
            re.fullmatch(r"[0-9a-z?/:@\-._~%!$&'()*+,;=#]*", fragment, re.IGNORECASE)
        )
    return optionalSegments


@validator
def url(
    value: str,
    /,
    *,
    skipIpv6Addr: bool = False,
    skipIpv4Addr: bool = False,
    mayHavePort: bool = True,
    simpleHost: bool = False,
    strictQuery: bool = True,
    considerTld: bool = False,
    private: Optional[bool] = None,  # only for ip-addresses
    rfc1034: bool = False,
    rfc2782: bool = False,
    validateScheme: Callable[[str], bool] = _validateScheme,
):
    r"""Return whether or not given value is a valid URL.

    This validator was originally inspired from [URL validator of dperini][1].
    The following diagram is from [urlly][2]::


            foo://admin:hunter1@example.com:8042/over/there?name=ferret#nose
            \_/   \___/ \_____/ \_________/ \__/\_________/ \_________/ \__/
             |      |       |       |        |       |          |         |
          scheme username password hostname port    path      query    fragment

    [1]: https://gist.github.com/dperini/729294
    [2]: https://github.com/treeform/urlly

    Examples:
        >>> url('http://duck.com')
        True
        >>> url('ftp://foobar.dk')
        True
        >>> url('http://10.0.0.1')
        True
        >>> url('http://example.com/">user@example.com')
        ValidationError(func=url, args={'value': 'http://example.com/">user@example.com'})

    Args:
        value:
            URL string to validate.
        skip_ipv6_addr:
            When URL string cannot contain an IPv6 address.
        skip_ipv4_addr:
            When URL string cannot contain an IPv4 address.
        may_have_port:
            URL string may contain port number.
        simple_host:
            URL string maybe only hyphens and alpha-numerals.
        strict_query:
            Fail validation on query string parsing error.
        consider_tld:
            Restrict domain to TLDs allowed by IANA.
        private:
            Embedded IP address is public if `False`, private/local if `True`.
        rfc_1034:
            Allow trailing dot in domain/host name.
            Ref: [RFC 1034](https://www.rfc-editor.org/rfc/rfc1034).
        rfc_2782:
            Domain/Host name is of type service record.
            Ref: [RFC 2782](https://www.rfc-editor.org/rfc/rfc2782).
        validate_scheme:
            Function that validates URL scheme.

    Returns:
        (Literal[True]): If `value` is a valid url.
        (ValidationError): If `value` is an invalid url.
    """
    if not value or re.search(r"\s", value):
        # url must not contain any white
        # spaces, they must be encoded
        return False

    try:
        scheme, netloc, path, query, fragment = urlsplit(value)
    except ValueError:
        return False

    return (
        validateScheme(scheme)
        and _validateNetloc(
            netloc,
            skipIpv6Addr,
            skipIpv4Addr,
            mayHavePort,
            simpleHost,
            considerTld,
            private,
            rfc1034,
            rfc2782,
        )
        and _validateOptionals(path, query, fragment, strictQuery)
    )
