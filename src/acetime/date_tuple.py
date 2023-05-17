# Copyright 2018 Brian T. Park
#
# MIT License

"""
Internal date-time component classes needed to handle hours in the form 24:00 or
25:00 (which cannot be handled by datetime.time, or to make certain calculations
easier.
"""

import logging
from datetime import datetime
from datetime import timedelta
from datetime import date
from typing import NamedTuple

from .common import MIN_YEAR
from .common import hms_to_seconds
from .common import seconds_to_hms


class DateTuple(NamedTuple):
    """A datetime representation using seconds instead of h:m:s. I think this
    class makes arithmetic operations on this easier.
    """
    y: int  # year
    M: int  # month
    d: int  # day
    ss: int  # total number of seconds
    f: str  # modifier ('w', 's', 'u')


def subtract_date_tuple(a: DateTuple, b: DateTuple) -> int:
    """Number of seconds in (a - b), ignoring the 'format' field.
    """
    da = date(a.y, a.M, a.d)
    db = date(b.y, b.M, b.d)
    diff_days = da.toordinal() - db.toordinal()
    diff_seconds = a.ss - b.ss
    return diff_days * 86400 + diff_seconds


def datetime_to_datetuple(dt: datetime, format: str) -> DateTuple:
    """Create a DateTuple from the given 'datetime' along with the 'format'
    modifer ('s', 'u', 'w').
    """
    secs = hms_to_seconds(dt.hour, dt.minute, dt.second)
    return DateTuple(y=dt.year, M=dt.month, d=dt.day, ss=secs, f=format)


def normalize_date_tuple(tt: DateTuple) -> DateTuple:
    """Return the normalized DateTuple where the dt.ss could be negative or
    greater than 24h. Throws exception if the normalization fails.
    TODO: Reimplement logic of ExtendedZoneProcessor::normalizeDateTuple().
    """
    if tt.y == MIN_YEAR:
        return DateTuple(y=MIN_YEAR, M=1, d=1, ss=0, f=tt.f)

    try:
        st = datetime(tt.y, tt.M, tt.d)
        delta = timedelta(seconds=tt.ss)
        st += delta
        return datetime_to_datetuple(st, tt.f)
    except:  # noqa: E722
        logging.error('Invalid datetime: %s + %s', st, delta)
        raise


def date_tuple_to_string(dt: DateTuple) -> str:
    (h, m, s) = seconds_to_hms(dt.ss)
    return f'{dt.y:04}-{dt.M:02}-{dt.d:02}T{h:02}:{m:02}{dt.f}'


class YearMonthTuple(NamedTuple):
    """A tuple of (year, month)"""
    y: int
    M: int
