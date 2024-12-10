# Copyright 2021 Brian T. Park
#
# MIT License

"""
Common constants and low-level functions shared by various modules in this
package:

* acetz.py
* transition.py
* date_tuple.py
* zone_processor.py
"""

from typing import Tuple
import datetime


# Sentinel year that is guaranteed not to appear in a zonedb entry.
# Often used by a function to indicate that the result was not found.
INVALID_YEAR: int = -32768

# Marker year in a zonedb entry to indicate -Infinity year.
MIN_YEAR: int = -32767

# Marker year in a zonedb entry to indicate +Infinity for UNTIL year.
MAX_UNTIL_YEAR: int = 32767

# Marker year in a zonedb entry to indicate +Infinity for TO year.
MAX_TO_YEAR: int = MAX_UNTIL_YEAR - 1

# Epoch Year used by this library. Early version used 2000. Changed to 2050 to
# be more compatible with AceTime v2, mostly for debugging purposes.
EPOCH_YEAR: int = 2050

# Number of seconds from Python Epoch (Unix epoch of 1970-01-01 00:00:00) to
# Epoch Year.
SECONDS_SINCE_UNIX_EPOCH = int(datetime.datetime(
    EPOCH_YEAR, 1, 1, tzinfo=datetime.timezone.utc).timestamp())


def to_epoch_seconds(unix_seconds: int) -> int:
    """Convert unix seconds to internal epoch seconds."""
    return unix_seconds - SECONDS_SINCE_UNIX_EPOCH


def to_unix_seconds(epoch_seconds: int) -> int:
    """Convert internal epoch seconds to unix seconds."""
    return epoch_seconds + SECONDS_SINCE_UNIX_EPOCH


def seconds_to_hms(seconds: int) -> Tuple[int, int, int]:
    """Convert seconds to (h,m,s). Works only for positive seconds.
    """
    s = seconds % 60
    minutes = seconds // 60
    m = minutes % 60
    h = minutes // 60
    return (h, m, s)


def hms_to_seconds(h: int, m: int, s: int) -> int:
    """Convert h:m:s to seconds.
    """
    return (h * 60 + m) * 60 + s


def calc_day_of_month(
    year: int,
    month: int,
    on_day_of_week: int,
    on_day_of_month: int,
) -> Tuple[int, int]:
    """Return the actual (month, day) of expressions such as
    (on_day_of_week >= on_day_of_month), (on_day_of_week <= on_day_of_month), or
    (lastMon) See calcStartDayOfMonth() in AceTime/src/ace_time/ZoneProcessor.h.
    Shifts into previous or next month can occur.

    Return (13, xx) if a shift to the next year occurs
    Return (0, xx) if a shift to the previous year occurs
    """
    if on_day_of_week == 0:
        return (month, on_day_of_month)

    if on_day_of_month >= 0:
        days_in_month = days_in_year_month(year, month)

        # Handle lastXxx by transforming it into (Xxx >= (daysInMonth - 6))
        if on_day_of_month == 0:
            on_day_of_month = days_in_month - 6

        limit_date = datetime.date(year, month, on_day_of_month)
        day_of_week_shift = (on_day_of_week - limit_date.isoweekday() + 7) % 7
        day = on_day_of_month + day_of_week_shift
        if day > days_in_month:
            day -= days_in_month
            month += 1
        return (month, day)
    else:
        on_day_of_month = -on_day_of_month
        limit_date = datetime.date(year, month, on_day_of_month)
        day_of_week_shift = (limit_date.isoweekday() - on_day_of_week + 7) % 7
        day = on_day_of_month - day_of_week_shift
        if day < 1:
            month -= 1
            days_in_prev_month = days_in_year_month(year, month)
            day += days_in_prev_month
        return (month, day)


def days_in_year_month(year: int, month: int) -> int:
    """Return the number of days in the given (year, month). The
    month is usually 1-12, but can be 0 to indicate December of the previous
    year, and 13 to indicate Jan of the following year.
    """
    DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    is_leap = (year % 4 == 0) and ((year % 100 != 0) or (year % 400) == 0)
    days = DAYS_IN_MONTH[(month - 1) % 12]
    if month == 2:
        days += is_leap
    return days


def to_utc_string(stdoffset: int, dstoffset: int) -> str:
    """Return (std,dst) pair as UTC{+/-hh:mm}{+/-hh:mm} (e.g.
    UTC-08:00+01:00). Intended for debugging purposes.
    """
    return (
        'UTC'
        f'{seconds_to_hm_string(stdoffset)}'
        f'{seconds_to_hm_string(dstoffset)}'
    )


def seconds_to_hm_string(secs: int) -> str:
    """Return secs as +/-hh:mm (e.g. -08:00)"""
    if secs < 0:
        hms = seconds_to_hms(-secs)
        return f'-{hms[0]:02}:{hms[1]:02}'
    else:
        hms = seconds_to_hms(secs)
        return f'+{hms[0]:02}:{hms[1]:02}'


def seconds_to_abbrev(secs: int) -> str:
    """Convert total UTC offset seconds to a timezone abbreviation according to
    the %z format: [+/-]hh[mm[ss]] using the shortest form that does not lose
    information.
    """
    s = secs if secs >= 0 else -secs
    hms = seconds_to_hms(s)

    abbrev = '+' if secs >= 0 else '-'
    abbrev += f'{hms[0]:02}'
    if hms[1] != 0 or hms[2] != 0:
        abbrev += f'{hms[1]:02}'
    if hms[2] != 0:
        abbrev += f'{hms[2]:02}'
    return abbrev
