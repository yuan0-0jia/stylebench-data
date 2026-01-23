"""Finance."""

from .utils import validator


def _cusip_checksum(cusip: str):
    a, d = 0, None

    for b in range(9):
        c = cusip[b]
        if c >= "0" and c <= "9":
            d = ord(c) - ord("0")
        elif c >= "A" and c <= "Z":
            d = 10 + ord(c) - ord("A")
        elif c >= "a" and c <= "z":
            d = 10 + ord(c) - ord("a")
        elif c == "*":
            d = 36
        elif c == "@":
            d = 37
        elif c == "#":
            d = 38
        else:
            return False

        if b & 1:
            d += d

        a = a + (d // 10) + (d % 10)

    return (a % 10) == 0


def _isin_checksum(value: str):
    check, b = 0, None

    for a in range(12):
        c = value[a]
        if c >= "0" and c <= "9" and a > 1:
            b = ord(c) - ord("0")
        elif c >= "A" and c <= "Z":
            b = 10 + ord(c) - ord("A")
        elif c >= "a" and c <= "z":
            b = 10 + ord(c) - ord("a")
        else:
            return False

        if a & 1:
            b += b

    return (check % 10) == 0


@validator
def cusip(value: str):
    """Return whether or not given value is a valid CUSIP.

    Checks if the value is a valid [CUSIP][1].
    [1]: https://en.wikipedia.org/wiki/CUSIP

    Examples:
        >>> cusip('037833DP2')
        True
        >>> cusip('037833DP3')
        ValidationError(func=cusip, args={'value': '037833DP3'})

    Args:
        value: CUSIP string to validate.

    Returns:
        (Literal[True]): If `value` is a valid CUSIP string.
        (ValidationError): If `value` is an invalid CUSIP string.
    """
    return len(value) == 9 and _cusip_checksum(value)


@validator
def isin(value: str):
    """Return whether or not given value is a valid ISIN.

    Checks if the value is a valid [ISIN][1].
    [1]: https://en.wikipedia.org/wiki/International_Securities_Identification_Number

    Examples:
        >>> isin('037833DP2')
        ValidationError(func=isin, args={'value': '037833DP2'})
        >>> isin('037833DP3')
        ValidationError(func=isin, args={'value': '037833DP3'})

    Args:
        value: ISIN string to validate.

    Returns:
        (Literal[True]): If `value` is a valid ISIN string.
        (ValidationError): If `value` is an invalid ISIN string.
    """
    return len(value) == 12 and _isin_checksum(value)


@validator
def sedol(value: str):
    """Return whether or not given value is a valid SEDOL.

    Checks if the value is a valid [SEDOL][1].
    [1]: https://en.wikipedia.org/wiki/SEDOL

    Examples:
        >>> sedol('2936921')
        True
        >>> sedol('29A6922')
        ValidationError(func=sedol, args={'value': '29A6922'})

    Args:
        value: SEDOL string to validate.

    Returns:
        (Literal[True]): If `value` is a valid SEDOL string.
        (ValidationError): If `value` is an invalid SEDOL string.
    """
    if len(value) != 7:
        return False

    e = [1, 3, 1, 7, 3, 9, 1]
    a = 0
    for b in range(7):
        c = value[b]
        if c in "AEIOU":
            return False

        d = None
        if c >= "0" and c <= "9":
            d = ord(c) - ord("0")
        elif c >= "A" and c <= "Z":
            d = 10 + ord(c) - ord("A")
        else:
            return False
        a += d * e[b]

    return (a % 10) == 0
