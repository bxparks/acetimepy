# Copyright 2020 Brian T. Park
#
# MIT License

from typing import Optional
from datetime import datetime, tzinfo, timedelta, timezone

from .common import to_epoch_seconds
from .zone_processor import ZoneProcessor
from .typing import ZoneInfo, ZoneInfoMap


class acetz(tzinfo):
    """An implementation of datetime.tzinfo using the ZoneProcessor class.
    """

    def __init__(self, zone_info: ZoneInfo):
        self.zp = ZoneProcessor(zone_info)

    def utcoffset(self, dt: Optional[datetime]) -> timedelta:
        assert dt
        info = self.zp.get_timezone_info_for_datetime(dt)
        if not info:
            raise Exception(
                f'Unknown timezone info for '
                f'{dt.year:04}-{dt.month:02}-{dt.day:02} '
                f'{dt.hour:02}:{dt.minute:02}:{dt.second:02}'
            )

        return timedelta(seconds=info.total_offset)

    def dst(self, dt: Optional[datetime]) -> timedelta:
        assert dt
        offset_info = self.zp.get_timezone_info_for_datetime(dt)
        if not offset_info:
            raise Exception(
                f'Unknown timezone info for '
                f'{dt.year:04}-{dt.month:02}-{dt.day:02} '
                f'{dt.hour:02}:{dt.minute:02}:{dt.second:02}'
            )
        return timedelta(seconds=offset_info.dst_offset)

    def tzname(self, dt: Optional[datetime]) -> str:
        """Return the abbreviation of the timezone, instead of the full name,
        for compatibility with other Python timezone libraries (pytz, dateutils,
        and zoneinfo). Use tzfullname() to get the full name of the time zone.
        """
        assert dt
        offset_info = self.zp.get_timezone_info_for_datetime(dt)
        if not offset_info:
            raise Exception(
                f'Unknown timezone info for '
                f'{dt.year:04}-{dt.month:02}-{dt.day:02} '
                f'{dt.hour:02}:{dt.minute:02}:{dt.second:02}'
            )
        return offset_info.abbrev

    def fromutc(self, dt: Optional[datetime]) -> datetime:
        """Override the default implementation in tzinfo which does not make
        sense for acetz.

        The 'dt' passed into this function from datetime.astimezone() is a weird
        one: the components are in UTC time, but the timezone is the target
        tzinfo, in other words, the same acetz as self.

        Warning: Do NOT call dt.isoformat() from this method, because it causes
        an infinite recursion as it tries to figure out the UTC offset. Use
        {dt.date()} and {dt.time()} instead.
        """
        if not isinstance(dt, datetime):
            raise TypeError("fromutc() requires a datetime argument")
        if dt.tzinfo is not self:
            raise ValueError("dt.tzinfo is not self")

        # Extract the epoch_seconds of the source 'dt'
        assert dt
        utcdt = dt.replace(tzinfo=timezone.utc)
        unix_seconds = int(utcdt.timestamp())
        epoch_seconds = to_epoch_seconds(unix_seconds)

        # Search the transitions for the matching Transition
        offset_info = self.zp.get_timezone_info_for_seconds(epoch_seconds)
        if not offset_info:
            raise ValueError(
                f"transition not found for {epoch_seconds} ({utcdt})")

        # Convert the date/time fields into local date/time and attach
        # the current acetz object.
        newutcdt = utcdt + timedelta(seconds=offset_info.total_offset)
        newdt = newutcdt.replace(tzinfo=self, fold=offset_info.fold)

        return newdt

    def tzfullname(self) -> str:
        """Return the full name of the time zone. Use this instead of tzname()
        to get the full name (e.g. "America/Los_Angeles") instead of the
        abbreviation (e.g. "PST").
        """
        return self.zp.get_name()

    def targetname(self) -> str:
        """Return the name of the target Zone if the timezone is a Link.
        Otherwise return the empty string.
        """
        return self.zp.get_target_name()

    def islink(self) -> bool:
        return self.zp.is_link()

    def zone_processor(self) -> ZoneProcessor:
        return self.zp


class ZoneManager:
    """Factory of acetz instances using the given zone registry. Usually the
    zone registry will be either zone_registry.ZONE_REGISTRY or
    zone_registry.ZONE_AND_LINK_REGISTRY, but applications may define a custom
    registry instead.
    """
    def __init__(self, registry: ZoneInfoMap):
        self.registry = registry

    def gettz(self, zone_name: str) -> Optional[acetz]:
        """Return the acetz instance for the given zone_name, or None
        None if zone_name is not found. Returning None instead of raising an
        Exception is consistent with dateutil.tz.gettz().
        """
        zone_info = self.registry.get(zone_name)
        if not zone_info:
            return None
        return acetz(zone_info)
