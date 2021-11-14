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
START
Original timezones: 377
Common timezones: 377
Start year: 2000
Until year: 2038
BENCHMARKS
acetz: 343824 10.57
dateutil: 343824 6.21
pytz: 343824 19.78
END
"""

import logging
import time
from argparse import ArgumentParser
from typing import Iterable
from typing import Set
from typing import Optional
from typing import Tuple
import pytz
from pytz import BaseTzInfo
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
        print("START")
        print(f"Original timezones: {len(ZONE_REGISTRY)}")
        common_zones = self.find_common_zones()
        print(f"Common timezones: {len(common_zones)}")
        print(f"Start year: {self.start_year}")
        print(f"Until year: {self.until_year}")

        print("BENCHMARKS")
        count, elapsed = self.run_acetz(common_zones)
        self.print_result("acetz", count, elapsed)

        count, elapsed = self.run_dateutil(common_zones)
        self.print_result("dateutil", count, elapsed)

        count, elapsed = self.run_pytz(common_zones)
        self.print_result("pytz", count, elapsed)

        print("END")

    def print_result(self, label: str, count: int, elapsed: float) -> None:
        """Print label, count, and micros_per_iteration."""
        perf = elapsed * 1000000 / count
        print(f"{label}: {count} {perf:.2f}")

    def find_common_zones(self) -> Set[str]:
        """Find common zone names."""
        common_zones: Set[str] = set()
        tz: Optional[tzinfo]
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

        return common_zones

    def run_acetz(self, zones: Iterable[str]) -> Tuple[int, float]:
        """Return count and micros per iteration."""
        start = time.time()
        count = 0
        for name in zones:
            tz = self.zone_manager.gettz(name)
            assert tz is not None
            count += self.loop_components_to_epoch_tz(tz)
        elapsed = time.time() - start
        return count, elapsed

    def run_dateutil(self, zones: Iterable[str]) -> Tuple[int, float]:
        """Return count and micros per iteration."""
        start = time.time()
        count = 0
        for name in zones:
            tz = gettz(name)
            assert tz is not None
            count += self.loop_components_to_epoch_tz(tz)
        elapsed = time.time() - start
        return count, elapsed

    def run_pytz(self, zones: Iterable[str]) -> Tuple[int, float]:
        """Return count and micros per iteration."""
        start = time.time()
        count = 0
        for name in zones:
            tz = pytz.timezone(name)
            count += self.loop_components_to_epoch_pytz(tz)
        elapsed = time.time() - start
        return count, elapsed

    def loop_components_to_epoch_tz(self, tz: tzinfo) -> int:
        """Return number of iterations for given tz."""
        count = 0
        for year in range(self.start_year, self.until_year):
            for month in range(1, 13):
                for day in (1, 28):
                    count += 1
                    dt = datetime(year, month, day, 1, 2, 3, tzinfo=tz)
                    unix_seconds = int(dt.timestamp())
                    epoch_seconds = unix_seconds - SECONDS_SINCE_UNIX_EPOCH
                    epoch_seconds
        return count

    def loop_components_to_epoch_pytz(self, tz: BaseTzInfo) -> int:
        """Return elapsed millis per iteration for given pytz."""
        count = 0
        for year in range(self.start_year, self.until_year):
            for month in range(1, 13):
                for day in (1, 28):
                    count += 1
                    dt_wall = datetime(year, month, day, 1, 2, 3)
                    dt = tz.localize(dt_wall)
                    dt = tz.normalize(dt)
                    unix_seconds = int(dt.timestamp())
                    epoch_seconds = unix_seconds - SECONDS_SINCE_UNIX_EPOCH
                    epoch_seconds
        return count


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
