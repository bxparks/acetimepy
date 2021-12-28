# Copyright 2021 Brian T. Park
#
# MIT License

"""
Compare timezone transitions between AceTimePython acetime.acetz and Python 3.9
zoneinfo, and print out a report of the discrepencies.
"""

import logging
from datetime import datetime, timedelta, timezone
from argparse import ArgumentParser
from typing import Any, Tuple, List

# Using sys.version_info works better for MyPy than using a try/except block.
import sys
if sys.version_info >= (3, 9):
    import zoneinfo
else:
    from backports import zoneinfo

# AceTimePython classes
from acetime.acetz import ZoneManager
from acetime.zonedb.zone_registry import ZONE_REGISTRY

# The [start, until) time interval used to search for DST transitions,
# and flag that is True if ONLY the DST changed.
TransitionTimes = Tuple[datetime, datetime, bool]


class Comparator():
    def __init__(
        self,
        start_year: int,
        until_year: int,
        sampling_interval: int,
        zone_manager: ZoneManager,
    ):
        self.start_year = start_year
        self.until_year = until_year
        self.sampling_interval = timedelta(hours=sampling_interval)
        self.zone_manager = zone_manager

    def compare_zone(self, zone_name: str) -> None:
        self.has_diff = False
        self.zone_name = zone_name

        zi_tz = zoneinfo.ZoneInfo(zone_name)
        if not zi_tz:
            logging.error(f"Zone '{zone_name}' not found in zoneinfo package")

        ace_tz = self.zone_manager.gettz(zone_name)
        if not ace_tz:
            logging.error(f"Zone '{zone_name}' not found in acetime package")

        self._diff_tz(zi_tz, ace_tz)

    def _diff_tz(self, zi_tz: Any, ace_tz: Any) -> None:
        """Add DST transitions, using 'A' and 'B' designators"""

        transitions = self._find_transitions(zi_tz)
        for (left, right, only_dst) in transitions:
            self._check_dt(left, ace_tz)
            self._check_dt(right, ace_tz)

    def _find_transitions(self, tz: Any) -> List[TransitionTimes]:
        """Find the DST transition using 'zoneinfo' package by sampling the time
        period from [start_year, until_year].
        """
        # TODO: Do I need to start 1 day before Jan 1 UTC, in case the
        # local time is ahead of UTC?
        dt = datetime(self.start_year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        dt_local = dt.astimezone(tz)

        # Check every 'sampling_interval' hours for a transition
        transitions: List[TransitionTimes] = []
        while True:
            next_dt = dt + self.sampling_interval
            next_dt_local = next_dt.astimezone(tz)
            if next_dt.year >= self.until_year:
                break

            # Look for a UTC or DST transition.
            if self.is_transition(dt_local, next_dt_local):
                # print(f'Transition between {dt_local} and {next_dt_local}')
                dt_left, dt_right = self._binary_search_transition(
                    tz, dt, next_dt)
                dt_left_local = dt_left.astimezone(tz)
                dt_right_local = dt_right.astimezone(tz)
                only_dst = self.only_dst(dt_left_local, dt_right_local)
                transitions.append((dt_left_local, dt_right_local, only_dst))

            dt = next_dt
            dt_local = next_dt_local

        return transitions

    def is_transition(self, dt1: datetime, dt2: datetime) -> bool:
        """Determine if dt1 -> dt2 is a UTC offset transition. If
        detect_dst_transition is True, then also detect DST offset transition.
        """
        if dt1.utcoffset() != dt2.utcoffset():
            return True
        return dt1.dst() != dt2.dst()

    def only_dst(self, dt1: datetime, dt2: datetime) -> bool:
        """Determine if dt1 -> dt2 is only a DST transition."""
        return dt1.utcoffset() == dt2.utcoffset() and dt1.dst() != dt2.dst()

    def _binary_search_transition(
        self,
        tz: Any,
        dt_left: datetime,
        dt_right: datetime,
    ) -> Tuple[datetime, datetime]:
        """Do a binary search to find the exact transition times, to within 1
        minute accuracy. The dt_left and dt_right are 22 hours (1320 minutes)
        apart. So the binary search should take a maximum of 11 iterations to
        find the DST transition within one adjacent minute.
        """
        dt_left_local = dt_left.astimezone(tz)
        while True:
            delta_minutes = int((dt_right - dt_left) / timedelta(minutes=1))
            delta_minutes //= 2
            if delta_minutes == 0:
                break

            dt_mid = dt_left + timedelta(minutes=delta_minutes)
            mid_dt_local = dt_mid.astimezone(tz)
            if self.is_transition(dt_left_local, mid_dt_local):
                dt_right = dt_mid
            else:
                dt_left = dt_mid
                dt_left_local = mid_dt_local

        return dt_left, dt_right

    def _check_dt(self, dt: datetime, ace_tz: Any) -> None:
        """Check that the given 'dt' matches the datetime using the given tz.
        """

        # Extract the components of the zoneinfo version of datetime.
        unix_seconds = int(dt.timestamp())
        total_offset = int(dt.utcoffset().total_seconds())  # type: ignore
        dst_offset = int(dt.dst().total_seconds())  # type: ignore
        # See https://stackoverflow.com/questions/5946499 for more info on how
        # to extract the abbreviation. dt.tzinfo will never be None because the
        # timezone will always be defined.
        assert dt.tzinfo is not None
        abbrev = dt.tzinfo.tzname(dt)

        # Extract the components of the acetz version of datetime.
        expected = dt.astimezone(ace_tz)
        expected_unix_seconds = int(expected.timestamp())
        expected_total_offset = int(
            expected.utcoffset().total_seconds()  # type: ignore
        )
        expected_dst_offset = int(
            expected.dst().total_seconds()  # type: ignore
        )
        assert expected.tzinfo is not None
        expected_abbrev = expected.tzinfo.tzname(expected)

        # Compare the two date times.
        if unix_seconds != expected_unix_seconds:
            raise Exception(
                "Unexpected mismatch of unix seconds: {self.zone_name}: "
                f"{unix_seconds}, {expected_unix_seconds}"
            )
        if dst_offset != expected_dst_offset:
            self.print_variance(
                "dst_offset",
                unix_seconds,
                dt,
                expected_dst_offset,
                dst_offset,
            )
        if total_offset != expected_total_offset:
            self.print_variance(
                "total_offset",
                unix_seconds,
                dt,
                expected_total_offset,
                total_offset,
            )
        if dt.year != expected.year:
            self.print_variance(
                "year",
                unix_seconds,
                dt,
                expected.year,
                dt.year,
            )
        if dt.month != expected.month:
            self.print_variance(
                "month",
                unix_seconds,
                dt,
                expected.month,
                dt.month,
            )
        if dt.day != expected.day:
            self.print_variance(
                "day",
                unix_seconds,
                dt,
                expected.day,
                dt.day,
            )
        if dt.hour != expected.hour:
            self.print_variance(
                "hour",
                unix_seconds,
                dt,
                expected.hour,
                dt.hour,
            )
        if dt.minute != expected.minute:
            self.print_variance(
                "minute",
                unix_seconds,
                dt,
                expected.minute,
                dt.minute,
            )
        if dt.second != expected.second:
            self.print_variance(
                "second",
                unix_seconds,
                dt,
                expected.second,
                dt.second,
            )
        if abbrev != expected_abbrev:
            self.print_variance(
                "abbrev",
                unix_seconds,
                dt,
                expected_abbrev,
                abbrev,
            )

    def print_variance(
        self,
        label: str,
        unix_seconds: int,
        dt: datetime,
        expected: Any,
        got: Any,
    ) -> None:
        # Print zone on the first variance
        if not self.has_diff:
            print(f"Zone {self.zone_name}")
            self.has_diff = True

        print(f"{unix_seconds}: {dt}: {label}: expected {expected}, got {got}")


def main() -> None:
    parser = ArgumentParser(description='Compare acetime and zoneinfo.')

    parser.add_argument(
        '--start_year',
        help='Start year of validation (default: start_year)',
        type=int,
        default=1974)
    parser.add_argument(
        '--until_year',
        help='Until year of validation (default: 2050)',
        type=int,
        default=2050)
    parser.add_argument(
        '--sampling_interval',
        type=int,
        default=22,
        help='Sampling interval in hours (default 22)',
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    zone_manager = ZoneManager(ZONE_REGISTRY)
    comparator = Comparator(
        start_year=args.start_year,
        until_year=args.until_year,
        sampling_interval=args.sampling_interval,
        zone_manager=zone_manager,
    )
    for zone_name, zone_info in ZONE_REGISTRY.items():
        comparator.compare_zone(zone_name)


if __name__ == '__main__':
    main()
