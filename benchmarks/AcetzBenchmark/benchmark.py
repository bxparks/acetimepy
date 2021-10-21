#!/usr/bin/env python3
#
# Copyright 2021 Brian T. Park
#
# MIT License

"""
Determines the speed of acetz class from AceTimePython library, compared to pytz
and dateutil.

Usage:

    $ ./benchmark.py [--start_year start] [--until_year until]

Expected output:

    Original timezones: 377
    Common timezones: 376
    acetz: 3.42
    dateutil: 1.91
    pytz: 5.99
"""

import logging
import time
from argparse import ArgumentParser
from typing import Iterable
from typing import Set
import pytz
from datetime import tzinfo
from datetime import datetime
from dateutil.tz import gettz

from acetime.acetz import ZoneManager
from acetime.zonedbpy.zone_registry import ZONE_REGISTRY
from acetime.common import SECONDS_SINCE_UNIX_EPOCH


class Benchmark:
    def __init__(
        self,
        start_year: int,
        until_year: int,
    ):
        self.start_year = start_year
        self.until_year = until_year
        self.zone_manager = ZoneManager(ZONE_REGISTRY)

    def run(self) -> None:
        print(f"Original timezones: {len(ZONE_REGISTRY)}")

        # Find common zone names.
        common_zones: Set[str] = set()
        for name, zone_info in ZONE_REGISTRY.items():
            # pytz
            try:
                tz = pytz.timezone(name)
            except pytz.UnknownTimeZoneError:
                continue

            # dateutil
            try:
                # The docs is silent on the behavior of gettz() when the name is
                # not a valid timezone. Handle both None and exception.
                tz = gettz(name)
                if tz is None:
                    continue
            except:  # noqa E722
                continue
            common_zones.add(name)

        print(f"Common timezones: {len(common_zones)}")
        self.run_acetz(common_zones)
        self.run_dateutil(common_zones)
        self.run_pytz(common_zones)

    def run_acetz(self, zones: Iterable) -> None:
        start = time.time()
        for name in zones:
            tz = self.zone_manager.gettz(name)
            self.loop_with_tz(tz)
        elapsed = time.time() - start
        print(f"acetz: {elapsed:.2f}")

    def run_dateutil(self, zones: Iterable) -> None:
        start = time.time()
        for name in zones:
            tz = gettz(name)
            self.loop_with_tz(tz)
        elapsed = time.time() - start
        print(f"dateutil: {elapsed:.2f}")

    def run_pytz(self, zones: Iterable) -> None:
        start = time.time()
        for name in zones:
            tz = pytz.timezone(name)
            self.loop_with_pytz(tz)
        elapsed = time.time() - start
        print(f"pytz: {elapsed:.2f}")

    def loop_with_tz(self, tz: tzinfo) -> None:
        """Run the benchmark for given tz."""
        for year in range(self.start_year, self.until_year):
            for month in range(1, 12):
                for day in (1, 28):
                    dt = datetime(year, month, day, 1, 2, 3, tzinfo=tz)
                    unix_seconds = int(dt.timestamp())
                    epoch_seconds = unix_seconds - SECONDS_SINCE_UNIX_EPOCH
                    epoch_seconds

    def loop_with_pytz(self, tz: tzinfo) -> None:
        """Run the benchmark for pytz, which requires special handling."""
        for year in range(self.start_year, self.until_year):
            for month in range(1, 12):
                for day in (1, 28):
                    dt_wall = datetime(year, month, day, 1, 2, 3)
                    dt = tz.localize(dt_wall)
                    dt = tz.normalize(dt)
                    unix_seconds = int(dt.timestamp())
                    epoch_seconds = unix_seconds - SECONDS_SINCE_UNIX_EPOCH
                    epoch_seconds


def main() -> None:
    parser = ArgumentParser(description='Benchmark Python timezone libs.')

    parser.add_argument(
        '--start_year',
        help='Start year of validation (default: start_year)',
        type=int,
        default=2000)
    parser.add_argument(
        '--until_year',
        help='Until year of validation (default: 2038)',
        type=int,
        default=2038)

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    benchmark = Benchmark(
        start_year=args.start_year,
        until_year=args.until_year,
    )
    benchmark.run()


if __name__ == '__main__':
    main()
