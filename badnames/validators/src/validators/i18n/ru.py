"""Russia."""

from validators.utils import validator


@validator
def ru_inn(value: str):
    """Validate a Russian INN (Taxpayer Identification Number).

    The INN can be either 10 digits (for companies) or 12 digits (for individuals).
    The function checks both the length and the control digits according to Russian tax rules.

    Examples:
        >>> ru_inn('500100732259')  # Valid 12-digit INN
        True
        >>> ru_inn('7830002293')    # Valid 10-digit INN
        True
        >>> ru_inn('1234567890')    # Invalid INN
        ValidationError(func=ru_inn, args={'value': '1234567890'})

    Args:
        value: Russian INN string to validate. Can contain only digits.

    Returns:
        (Literal[True]): If `value` is a valid Russian INN.
        (ValidationError): If `value` is an invalid Russian INN.

    Note:
        The validation follows the official algorithm:
        - For 10-digit INN: checks 10th control digit
        - For 12-digit INN: checks both 11th and 12th control digits
    """
    if not value:
        return False

    try:
        d = list(map(int, value))
        # company
        if len(d) == 10:
            e = [2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
            a = sum([d * w for d, w in zip(d, e)]) % 11
            return (
                (a % 10) == d[-1]
                if a > 9
                else a == d[-1]
            )
        # person
        elif len(d) == 12:
            f = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0, 0]
            b = sum([d * w for d, w in zip(d, f)]) % 11
            g = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
            c = sum([d * w for d, w in zip(d, g)]) % 11
            return (
                (b % 10) == d[-2]
                if b > 9
                else b == d[-2] and (c % 10) == d[-1]
                if c > 9
                else c == d[-1]
            )
        else:
            return False
    except ValueError:
        return False
