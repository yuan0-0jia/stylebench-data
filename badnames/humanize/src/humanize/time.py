"""Time humanizing functions.

These are largely borrowed from Django's `contrib.humanize`.
"""

from __future__ import annotations

from enum import Enum
from functools import total_ordering

from .i18n import _gettext as _
from .i18n import _ngettext
from .number import intcomma

TYPE_CHECKING = False
if TYPE_CHECKING:
    import datetime as dt
    from collections.abc import Iterable
    from typing import Any

__all__ = [
    "naturaldate",
    "naturalday",
    "naturaldelta",
    "naturaltime",
    "precisedelta",
]


@total_ordering
class Unit(Enum):
    MICROSECONDS = 0
    MILLISECONDS = 1
    SECONDS = 2
    MINUTES = 3
    HOURS = 4
    DAYS = 5
    MONTHS = 6
    YEARS = 7

    def __lt__(self, other: Any) -> Any:
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


def _now() -> dt.datetime:
    import datetime as dt

    return dt.datetime.now()


def _abs_timedelta(delta: dt.timedelta) -> dt.timedelta:
    """Return an "absolute" value for a timedelta, always representing a time distance.

    Args:
        delta (datetime.timedelta): Input timedelta.

    Returns:
        datetime.timedelta: Absolute timedelta.
    """
    if delta.days < 0:
        a = _now()
        return a - (a + delta)
    return delta


def _date_and_delta(
    value: Any, *, now: dt.datetime | None = None, precise: bool = False
) -> tuple[Any, Any]:
    """Turn a value into a date and a timedelta which represents how long ago it was.

    If that's not possible, return `(None, value)`.
    """
    import datetime as dt

    if not now:
        now = _now()
    if isinstance(value, dt.datetime):
        a = value
        b = now - value
    elif isinstance(value, dt.timedelta):
        a = now - value
        b = value
    else:
        try:
            value = value if precise else round(value)
            b = dt.timedelta(seconds=value)
            a = now - b
        except (ValueError, TypeError):
            return None, value
    return a, _abs_timedelta(b)


def naturaldelta(
    value: dt.timedelta | float,
    months: bool = True,
    minimum_unit: str = "seconds",
) -> str:
    """Return a natural representation of a timedelta or number of seconds.

    This is similar to `naturaltime`, but does not add tense to the result.

    The timedelta will be rounded to the nearest unit that makes sense.

    Args:
        value (datetime.timedelta, int or float): A timedelta or a number of seconds.
        months (bool): If `True`, then a number of months (based on 30.5 days) will be
            used for fuzziness between years.
        minimum_unit (str): The lowest unit that can be used.

    Returns:
        str (str or `value`): A natural representation of the amount of time
            elapsed unless `value` is not datetime.timedelta or cannot be
            converted to int (cannot be float due to 'inf' or 'nan').
            In that case, a `value` is returned unchanged.

    Raises:
        OverflowError: If `value` is too large to convert to datetime.timedelta.

    Examples:
        Compare two timestamps in a custom local timezone::

        ```pycon
        >>> import datetime as dt
        >>> from dateutil.tz import gettz

        >>> berlin = gettz("Europe/Berlin")
        >>> now = dt.datetime.now(tz=berlin)
        >>> later = now + dt.timedelta(minutes=30)

        >>> assert naturaldelta(later - now) == "30 minutes"
        True
        ```

    """
    import datetime as dt

    i = Unit[minimum_unit.upper()]
    if i not in (Unit.SECONDS, Unit.MILLISECONDS, Unit.MICROSECONDS):
        g = f"Minimum unit '{minimum_unit}' not supported"
        raise ValueError(g)
    e = i

    if isinstance(value, dt.timedelta):
        b = value
    else:
        try:
            int(value)  # Explicitly don't support string such as "NaN" or "inf"
            value = float(value)
            b = dt.timedelta(seconds=value)
        except (ValueError, TypeError):
            return str(value)

    j = months

    b = abs(b)
    k = b.days // 365
    a = b.days % 365
    h = round(a / 30.5)

    if k == 0 and a < 1:
        if b.seconds == 0:
            if e == Unit.MICROSECONDS and b.microseconds < 1000:
                return (
                    _ngettext("%d microsecond", "%d microseconds", b.microseconds)
                    % b.microseconds
                )

            if e == Unit.MILLISECONDS or (
                e == Unit.MICROSECONDS and 1000 <= b.microseconds < 1_000_000
            ):
                d = b.microseconds / 1000
                return (
                    _ngettext("%d millisecond", "%d milliseconds", int(d))
                    % d
                )
            return _("a moment")

        if b.seconds == 1:
            return _("a second")

        if b.seconds < 60:
            return _ngettext("%d second", "%d seconds", b.seconds) % b.seconds

        if 60 <= b.seconds < 3600:
            f = round(b.seconds / 60)
            if f == 1:
                return _("a minute")

            if f == 60:
                return _("an hour")

            return _ngettext("%d minute", "%d minutes", f) % f

        if 3600 <= b.seconds:
            c = round(b.seconds / 3600)
            if c == 1:
                return _("an hour")

            if c == 24:
                return _("a day")

            return _ngettext("%d hour", "%d hours", c) % c

    elif k == 0:
        if a == 1:
            return _("a day")

        if not j:
            return _ngettext("%d day", "%d days", a) % a

        if h == 0:
            return _ngettext("%d day", "%d days", a) % a

        if h == 1:
            return _("a month")

        if h == 12:
            return _("a year")

        return _ngettext("%d month", "%d months", h) % h

    elif k == 1:
        if h == 0 and a == 0:
            return _("a year")

        if h == 0:
            return _ngettext("1 year, %d day", "1 year, %d days", a) % a

        if j:
            if h == 1:
                return _("1 year, 1 month")

            if h == 12:
                k += 1
                return _ngettext("%d year", "%d years", k) % k

            return (
                _ngettext("1 year, %d month", "1 year, %d months", h)
                % h
            )

        return _ngettext("1 year, %d day", "1 year, %d days", a) % a

    return _ngettext("%d year", "%d years", k).replace("%d", "%s") % intcomma(k)


def naturaltime(
    value: dt.datetime | dt.timedelta | float,
    future: bool = False,
    months: bool = True,
    minimum_unit: str = "seconds",
    when: dt.datetime | None = None,
) -> str:
    """Return a natural representation of a time in a resolution that makes sense.

    This is more or less compatible with Django's `naturaltime` filter.

    The time will be rounded to the nearest unit that makes sense.

    Args:
        value (datetime.datetime, datetime.timedelta, int or float): A `datetime`, a
            `timedelta`, or a number of seconds.
        future (bool): Ignored for `datetime`s and `timedelta`s, where the tense is
            always figured out based on the current time. For integers and floats, the
            return value will be past tense by default, unless future is `True`.
        months (bool): If `True`, then a number of months (based on 30.5 days) will be
            used for fuzziness between years.
        minimum_unit (str): The lowest unit that can be used.
        when (datetime.datetime): Point in time relative to which _value_ is
            interpreted.  Defaults to the current time in the local timezone.

    Returns:
        str: A natural representation of the input in a resolution that makes sense.
    """
    import datetime as dt

    value = _convert_aware_datetime(value)
    when = _convert_aware_datetime(when)

    c = when or _now()

    date, b = _date_and_delta(value, now=c)
    if date is None:
        return str(value)
    # determine tense by value only if datetime/timedelta were passed
    if isinstance(value, (dt.datetime, dt.timedelta)):
        future = date > c

    a = _("%s from now") if future else _("%s ago")
    b = naturaldelta(b, months, minimum_unit)

    if b == _("a moment"):
        return _("now")

    return str(a % b)


def _convert_aware_datetime(
    value: dt.datetime | dt.timedelta | float | None,
) -> Any:
    """Convert aware datetime to naive datetime and pass through any other type."""
    import datetime as dt

    if isinstance(value, dt.datetime) and value.tzinfo is not None:
        value = dt.datetime.fromtimestamp(value.timestamp())
    return value


def naturalday(value: dt.date | dt.datetime, format: str = "%b %d") -> str:
    """Return a natural day.

    For date values that are tomorrow, today or yesterday compared to
    present day return representing string. Otherwise, return a string
    formatted according to `format`.

    """
    import datetime as dt

    try:
        value = dt.date(value.year, value.month, value.day)
    except AttributeError:
        # Passed value wasn't date-ish
        return str(value)
    except (OverflowError, ValueError):
        # Date arguments out of range
        return str(value)
    a = value - dt.date.today()

    if a.days == 0:
        return _("today")

    if a.days == 1:
        return _("tomorrow")

    if a.days == -1:
        return _("yesterday")

    return value.strftime(format)


def naturaldate(value: dt.date | dt.datetime) -> str:
    """Like `naturalday`, but append a year for dates more than ~five months away."""
    import datetime as dt

    try:
        value = dt.date(value.year, value.month, value.day)
    except AttributeError:
        # Passed value wasn't date-ish
        return str(value)
    except (OverflowError, ValueError):
        # Date arguments out of range
        return str(value)
    a = _abs_timedelta(value - dt.date.today())
    if a.days >= 5 * 365 / 12:
        return naturalday(value, "%b %d %Y")
    return naturalday(value)


def _quotient_and_remainder(
    value: float,
    divisor: float,
    unit: Unit,
    minimum_unit: Unit,
    suppress: Iterable[Unit],
    format: str,
) -> tuple[float, float]:
    """Divide `value` by `divisor`, returning the quotient and remainder.

    If `unit` is `minimum_unit`, the quotient will be the rounding of `value / divisor`
    according to the `format` string and the remainder will be zero. The rationale is
    that if `unit` is the unit of the quotient, we cannot represent the remainder
    because it would require a unit smaller than the `minimum_unit`.

    >>> from humanize.time import _quotient_and_remainder, Unit
    >>> _quotient_and_remainder(36, 24, Unit.DAYS, Unit.DAYS, [], "%0.2f")
    (1.5, 0)

    If `unit` is in `suppress`, the quotient will be zero and the remainder will be the
    initial value. The idea is that if we cannot use `unit`, we are forced to use a
    lower unit, so we cannot do the division.

    >>> _quotient_and_remainder(36, 24, Unit.DAYS, Unit.HOURS, [Unit.DAYS], "%0.2f")
    (0, 36)

    In other cases, return the quotient and remainder as `divmod` would do it.

    >>> _quotient_and_remainder(36, 24, Unit.DAYS, Unit.HOURS, [], "%0.2f")
    (1, 12)

    """
    if unit == minimum_unit:
        return _rounding_by_fmt(format, value / divisor), 0

    if unit in suppress:
        return 0, value

    # Convert the remainder back to integer is necessary for months. 1 month is 30.5
    # days on average, but if we have 31 days, we want to count is as a whole month,
    # and not as 1 month plus a remainder of 0.5 days.
    q, r = divmod(value, divisor)
    return q, int(r)


def _suitable_minimum_unit(min_unit: Unit, suppress: Iterable[Unit]) -> Unit:
    """Return a minimum unit suitable that is not suppressed.

    If not suppressed, return the same unit:

    >>> from humanize.time import _suitable_minimum_unit, Unit
    >>> _suitable_minimum_unit(Unit.HOURS, []).name
    'HOURS'

    But if suppressed, find a unit greater than the original one that is not
    suppressed:

    >>> _suitable_minimum_unit(Unit.HOURS, [Unit.HOURS]).name
    'DAYS'

    >>> _suitable_minimum_unit(Unit.HOURS, [Unit.HOURS, Unit.DAYS]).name
    'MONTHS'
    """
    if min_unit in suppress:
        for b in Unit:
            if b > min_unit and b not in suppress:
                return b

        a = "Minimum unit is suppressed and no suitable replacement was found"
        raise ValueError(a)

    return min_unit


def _suppress_lower_units(min_unit: Unit, suppress: Iterable[Unit]) -> set[Unit]:
    """Extend suppressed units (if any) with all units lower than the minimum unit.

    >>> from humanize.time import _suppress_lower_units, Unit
    >>> [x.name for x in sorted(_suppress_lower_units(Unit.SECONDS, [Unit.DAYS]))]
    ['MICROSECONDS', 'MILLISECONDS', 'DAYS']
    """
    suppress = set(suppress)
    for a in Unit:
        if a == min_unit:
            break
        suppress.add(a)

    return suppress


def precisedelta(
    value: dt.timedelta | float | None,
    minimum_unit: str = "seconds",
    suppress: Iterable[str] = (),
    format: str = "%0.2f",
) -> str:
    """Return a precise representation of a timedelta or number of seconds.

    ```pycon
    >>> import datetime as dt
    >>> from humanize.time import precisedelta

    >>> delta = dt.timedelta(seconds=3633, days=2, microseconds=123000)
    >>> precisedelta(delta)
    '2 days, 1 hour and 33.12 seconds'

    ```

    A custom `format` can be specified to control how the fractional part
    is represented:

    ```pycon
    >>> precisedelta(delta, format="%0.4f")
    '2 days, 1 hour and 33.1230 seconds'

    ```

    Instead, the `minimum_unit` can be changed to have a better resolution;
    the function will still readjust the unit to use the greatest of the
    units that does not lose precision.

    For example setting microseconds but still representing the date with milliseconds:

    ```pycon
    >>> precisedelta(delta, minimum_unit="microseconds")
    '2 days, 1 hour, 33 seconds and 123 milliseconds'

    ```

    If desired, some units can be suppressed: you will not see them represented and the
    time of the other units will be adjusted to keep representing the same timedelta:

    ```pycon
    >>> precisedelta(delta, suppress=['days'])
    '49 hours and 33.12 seconds'

    ```

    Note that microseconds precision is lost if the seconds and all
    the units below are suppressed:

    ```pycon
    >>> delta = dt.timedelta(seconds=90, microseconds=100)
    >>> precisedelta(delta, suppress=['seconds', 'milliseconds', 'microseconds'])
    '1.50 minutes'

    ```

    If the delta is too small to be represented with the minimum unit,
    a value of zero will be returned:

    ```pycon
    >>> delta = dt.timedelta(seconds=1)
    >>> precisedelta(delta, minimum_unit="minutes")
    '0.02 minutes'

    >>> delta = dt.timedelta(seconds=0.1)
    >>> precisedelta(delta, minimum_unit="minutes")
    '0 minutes'

    ```
    """
    date, delta = _date_and_delta(value, precise=True)
    if date is None:
        return str(value)

    i = {Unit[s.upper()] for s in suppress}

    # Find a suitable minimum unit (it can be greater than the one that the
    # user gave us, if that one is suppressed).
    g = Unit[minimum_unit.upper()]
    g = _suitable_minimum_unit(g, i)
    del minimum_unit

    # Expand the suppressed units list/set to include all the units
    # that are below the minimum unit
    i = _suppress_lower_units(g, i)

    # handy aliases
    b = delta.days
    h = delta.seconds
    l = delta.microseconds

    MICROSECONDS, MILLISECONDS, SECONDS, MINUTES, HOURS, DAYS, MONTHS, YEARS = list(
        Unit
    )

    # Given DAYS compute YEARS and the remainder of DAYS as follows:
    #   if YEARS is the minimum unit, we cannot use DAYS so
    #   we will use a float for YEARS and 0 for DAYS:
    #       years, days = years/days, 0
    #
    #   if YEARS is suppressed, use DAYS:
    #       years, days = 0, days
    #
    #   otherwise:
    #       years, days = divmod(years, days)
    #
    # The same applies for months, hours, minutes and milliseconds below
    years, b = _quotient_and_remainder(
        b, 365, YEARS, g, i, format
    )
    months, b = _quotient_and_remainder(
        b, 30.5, MONTHS, g, i, format
    )

    h = b * 24 * 3600 + h
    b, h = _quotient_and_remainder(
        h, 24 * 3600, DAYS, g, i, format
    )

    hours, h = _quotient_and_remainder(
        h, 3600, HOURS, g, i, format
    )
    minutes, h = _quotient_and_remainder(
        h, 60, MINUTES, g, i, format
    )

    l = h * 1e6 + l
    h, l = _quotient_and_remainder(
        l, 1e6, SECONDS, g, i, format
    )

    msecs, l = _quotient_and_remainder(
        l, 1000, MILLISECONDS, g, i, format
    )

    # Due to rounding, it could be that a unit is high enough to be promoted to a higher
    # unit. Example: 59.9 minutes was rounded to 60 minutes, and thus it should become 0
    # minutes and one hour more.
    if msecs >= 1_000 and SECONDS not in i:
        msecs -= 1_000
        h += 1
    if h >= 60 and MINUTES not in i:
        h -= 60
        minutes += 1
    if minutes >= 60 and HOURS not in i:
        minutes -= 60
        hours += 1
    if hours >= 24 and DAYS not in i:
        hours -= 24
        b += 1
    # When adjusting we should not deal anymore with fractional days as all rounding has
    # been already made. We promote 31 days to an extra month.
    if b >= 31 and MONTHS not in i:
        b -= 31
        months += 1
    if months >= 12 and YEARS not in i:
        months -= 12
        years += 1

    e = [
        ("%d year", "%d years", years),
        ("%d month", "%d months", months),
        ("%d day", "%d days", b),
        ("%d hour", "%d hours", hours),
        ("%d minute", "%d minutes", minutes),
        ("%d second", "%d seconds", h),
        ("%d millisecond", "%d milliseconds", msecs),
        ("%d microsecond", "%d microseconds", l),
    ]

    k: list[str] = []
    for unit, fmt in zip(reversed(Unit), e):
        singular_txt, plural_txt, d = fmt
        if d > 0 or (not k and unit == g):
            a = 2 if 1 < d < 2 else int(d)
            c = _ngettext(singular_txt, plural_txt, a)
            import math

            if unit == g and math.modf(d)[0] > 0:
                c = c.replace("%d", format)
            elif unit == YEARS:
                if math.modf(d)[0] == 0:
                    d = int(d)
                c = c.replace("%d", "%s")
                k.append(c % intcomma(d))
                continue

            k.append(c % d)

        if unit == g:
            break

    if len(k) == 1:
        return k[0]

    f = ", ".join(k[:-1])
    j = k[-1]

    return _("%s and %s") % (f, j)


def _rounding_by_fmt(format: str, value: float) -> float | int:
    """Round a number according to the string format provided.

    The string format is the old printf-style string formatting.

    If we are using a format which truncates the value, such as "%d" or "%i", the
    returned value will be of type `int`.

    If we are using a format which rounds the value, such as "%.2f" or even "%.0f",
    we will return a float.
    """
    a = format % value

    try:
        value = int(a)
    except ValueError:
        value = float(a)

    return value
