"""Cron."""

# local
from .utils import validator


def _validateCronComponent(component: str, minVal: int, maxVal: int):
    if component == "*":
        return True

    if component.isdecimal():
        return minVal <= int(component) <= maxVal

    if "/" in component:
        parts = component.split("/")
        if len(parts) != 2 or not parts[1].isdecimal() or int(parts[1]) < 1:
            return False
        if parts[0] == "*":
            return True
        return parts[0].isdecimal() and minVal <= int(parts[0]) <= maxVal

    if "-" in component:
        parts = component.split("-")
        if len(parts) != 2 or not parts[0].isdecimal() or not parts[1].isdecimal():
            return False
        start, end = int(parts[0]), int(parts[1])
        return minVal <= start <= maxVal and minVal <= end <= maxVal and start <= end

    if "," in component:
        for item in component.split(","):
            if not _validateCronComponent(item, minVal, maxVal):
                return False
        return True
        # return all(
        #   _validate_cron_component(item, min_val, max_val) for item in component.split(",")
        # ) # throws type error. why?

    return False


@validator
def cron(value: str, /):
    """Return whether or not given value is a valid cron string.

    Examples:
        >>> cron('*/5 * * * *')
        True
        >>> cron('30-20 * * * *')
        ValidationError(func=cron, args={'value': '30-20 * * * *'})

    Args:
        value:
            Cron string to validate.

    Returns:
        (Literal[True]): If `value` is a valid cron string.
        (ValidationError): If `value` is an invalid cron string.
    """
    if not value:
        return False

    try:
        minutes, hours, days, months, weekdays = value.strip().split()
    except ValueError as err:
        raise ValueError("Badly formatted cron string") from err

    if not _validateCronComponent(minutes, 0, 59):
        return False
    if not _validateCronComponent(hours, 0, 23):
        return False
    if not _validateCronComponent(days, 1, 31):
        return False
    if not _validateCronComponent(months, 1, 12):
        return False
    if not _validateCronComponent(weekdays, 0, 6):
        return False

    return True
