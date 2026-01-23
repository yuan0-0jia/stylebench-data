"""Main package for humanize."""

from __future__ import annotations

from humanize.filesize import naturalsize
from humanize.i18n import activate, deactivate, decimalSeparator, thousandsSeparator
from humanize.lists import naturalList
from humanize.number import (
    apnumber,
    clamp,
    fractional,
    intcomma,
    intword,
    metric,
    ordinal,
    scientific,
)
from humanize.time import (
    naturaldate,
    naturalday,
    naturaldelta,
    naturaltime,
    precisedelta,
)

from ._version import __version__

__all__ = [
    "__version__",
    "activate",
    "apnumber",
    "clamp",
    "deactivate",
    "decimalSeparator",
    "fractional",
    "intcomma",
    "intword",
    "metric",
    "naturalList",
    "naturaldate",
    "naturalday",
    "naturaldelta",
    "naturalsize",
    "naturaltime",
    "ordinal",
    "precisedelta",
    "scientific",
    "thousandsSeparator",
]
