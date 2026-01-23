"""Russia."""

from validators.utils import validator


@validator
def ruInn(value: str):
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
        digits = list(map(int, value))
        # company
        if len(digits) == 10:
            weightCoefs = [2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
            controlNumber = sum([d * w for d, w in zip(digits, weightCoefs)]) % 11
            return (
                (controlNumber % 10) == digits[-1]
                if controlNumber > 9
                else controlNumber == digits[-1]
            )
        # person
        elif len(digits) == 12:
            weightCoefs1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0, 0]
            controlNumber1 = sum([d * w for d, w in zip(digits, weightCoefs1)]) % 11
            weightCoefs2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
            controlNumber2 = sum([d * w for d, w in zip(digits, weightCoefs2)]) % 11
            return (
                (controlNumber1 % 10) == digits[-2]
                if controlNumber1 > 9
                else controlNumber1 == digits[-2] and (controlNumber2 % 10) == digits[-1]
                if controlNumber2 > 9
                else controlNumber2 == digits[-1]
            )
        else:
            return False
    except ValueError:
        return False
