#!/usr/bin/env python3.9
#
# Copyright 2021 Brian T. Park
#
# MIT License

"""
Determines the speed of acetz class from AceTimePython library, compared to
Python 3.9 zoneinfo library. For all zones (about 377 of them), two operations
are tested:

1. date components to unix seconds
2. unix seconds to date components

The raw benchmark numbers are given as 4 columns of numbers with a label, in the
format of:

    LABEL count1 micros1 count2 micros2

where

    count1 - number of date components to unix seconds conversions
    micros1 - micros per operation
    count2  - number of unix seconds to date components conversions
    micros2 - micros per operation

Usage:

$ ./benchmark.py [--start_year start] [--until_year until]
START
Original timezones: 377
Common timezones: 377
Start year: 2000
Until year: 2050
BENCHMARKS
acetz: 452400 10.902 459186 13.370
zoneinfo: 452400 1.434 459186 0.696
END

By default the start_year is 2000, and the until_year is 2050 because both
acetz and zoneinfo are able to handle dates after 2038.
"""

import logging
import time
from argparse import ArgumentParser
from typing import Iterable
from typing import Set
from typing import Optional
from typing import Tuple
from datetime import tzinfo
from datetime import datetime
from datetime import timezone
try:
    import zoneinfo  # type: ignore
except ImportError:
    from backports import zoneinfo

from acetime.acetz import ZoneManager
from acetime.zonedbpy.zone_registry import ZONE_REGISTRY


class Benchmark:
    def __init__(
        self,
        start_year: int,
        until_year: int,
    ):
        self.start_year = start_year
        self.until_year = until_year
        self.zone_manager = ZoneManager(ZONE_REGISTRY)

        # Find the start and until unix seconds

        dt_start = datetime(self.start_year, 1, 1, tzinfo=timezone.utc)
        self.start_unix_seconds = int(dt_start.timestamp())

        dt_until = datetime(self.until_year, 1, 1, tzinfo=timezone.utc)
        self.until_unix_seconds = int(dt_until.timestamp())

    def run(self) -> None:
        print("START")
        print(f"Original timezones: {len(ZONE_REGISTRY)}")
        common_zones = self.find_common_zones()
        print(f"Common timezones: {len(common_zones)}")
        print(f"Start year: {self.start_year}")
        print(f"Until year: {self.until_year}")

        print("BENCHMARKS")
        count1, elapsed1 = self.run_acetz(common_zones)
        count2, elapsed2 = self.run_acetz_epoch(common_zones)
        self.print_result("acetz", count1, elapsed1, count2, elapsed2)

        count1, elapsed1 = self.run_zoneinfo(common_zones)
        count2, elapsed2 = self.run_zoneinfo_epoch(common_zones)
        self.print_result(
            "zoneinfo", count1, elapsed1, count2, elapsed2)

        print("END")

    def print_result(
        self, label: str,
        count1: int,
        elapsed1: float,
        count2: int,
        elapsed2: float,
    ) -> None:
        """Print label, count, and micros_per_iteration."""
        perf1 = elapsed1 * 1000000 / count1
        perf2 = elapsed2 * 1000000 / count2
        print(f"{label}: {count1} {perf1:.3f} {count2} {perf2:.3f}")

    def find_common_zones(self) -> Set[str]:
        """Find common zone names."""
        common_zones: Set[str] = set()
        tz: Optional[tzinfo]
        for name, zone_info in ZONE_REGISTRY.items():
            # zoneinfo
            try:
                # The docs is silent on the behavior of gettz() when the name is
                # not a valid timezone. Handle both None and exception.
                tz = zoneinfo.ZoneInfo(name)
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

    def run_acetz_epoch(self, zones: Iterable[str]) -> Tuple[int, float]:
        """Return count and micros per iteration."""
        start = time.time()
        count = 0
        for name in zones:
            tz = self.zone_manager.gettz(name)
            assert tz is not None
            count += self.loop_epoch_to_components_tz(tz)
        elapsed = time.time() - start
        return count, elapsed

    def run_zoneinfo(self, zones: Iterable[str]) -> Tuple[int, float]:
        """Return count and micros per iteration."""
        start = time.time()
        count = 0
        for name in zones:
            tz = zoneinfo.ZoneInfo(name)
            assert tz is not None
            count += self.loop_components_to_epoch_tz(tz)
        elapsed = time.time() - start
        return count, elapsed

    def run_zoneinfo_epoch(self, zones: Iterable[str]) -> Tuple[int, float]:
        """Return count and micros per iteration."""
        start = time.time()
        count = 0
        for name in zones:
            tz = zoneinfo.ZoneInfo(name)
            assert tz is not None
            count += self.loop_epoch_to_components_tz(tz)
        elapsed = time.time() - start
        return count, elapsed

    def loop_components_to_epoch_tz(self, tz: tzinfo) -> int:
        """Return number of iterations for given tz."""
        count = 0
        for year in range(self.start_year, self.until_year):
            for month in range(1, 13):
                for day in (1, 28):  # check the 1st and the 28th
                    count += 1
                    dt = datetime(year, month, day, 1, 2, 3, tzinfo=tz)
                    int(dt.timestamp())
        return count

    def loop_epoch_to_components_tz(self, tz: tzinfo) -> int:
        """Return number of iterations for given tz."""
        count = 0
        for unix_seconds in range(
            self.start_unix_seconds,
            self.until_unix_seconds,
            15 * 86400,  # every 15 days
        ):
            count += 1
            datetime.fromtimestamp(unix_seconds, tz=tz)
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
        help='Until year of validation (default: 2050)',
        type=int,
        default=2050)

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
