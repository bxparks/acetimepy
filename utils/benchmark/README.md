# Acetz Benchmark

The `benchmark.py` script compares the speed of 4 timezone libraries:

* `acetime.timezone.acetz` from this project,
  [AceTimePython](https://github.com/bxparks/AceTimePython)
* `pytz.BaseTzInfo` from [pytz](https://pypi.org/project/pytz/)
* `dateutil.tz` from
  [python-dateutil](https://pypi.org/project/python-dateutil/)
* `zoneinfo.ZoneInfo` from
  [zoneinfo](https://docs.python.org/3/library/zoneinfo.html)
  backported to Python 3.8 and earlier using
  [backports.zoneinfo](https://pypi.org/project/backports.zoneinfo/)

There are 2 columns for each library in the table below:

* "comp to epoch": Measures the time to convert date-time components (yyyy-mm-dd
  hh:mm:ss) to epoch seconds.
* "epoch to comp": Measures the reverse mapping, from epoch seconds to date-time
  components.

The `benchmark.py` scans through all 377 timezones (as of TZDB 2021e), sampling
2 days for each month from the year 2000 until 2038. The numbers in the table
below is given units of microseconds per iteration, averaged over all timezones.

**Version**: AceTimePython v0.4.0

**NOTE**: This file was auto-generated using `make README.md`. DO NOT EDIT.

## Dependencies

This program depends on the following libraries:

* [AceTimePython](https://github.com/bxparks/AceTimePython)

## How to Generate

```
$ make benchmark.txt
$ make README.md
```

## Benchmark Changes

## Benchmarks

* Intel(R) Core(TM) i5-6300U CPU @ 2.40GHz
* Ubuntu 20.04.3 (LTS)
* Python 3.8.10

```
+-------------------+----------------+----------------+
| Time Zone Library | comp to epoch  | epoch to comp  |
|                   | (micros/iter)  | (micros/iter)  |
| acetime           |         10.963 |         13.475 |
| dateutil          |          5.960 |          7.257 |
| pytz              |         16.244 |         15.514 |
| zoneinfo          |          1.409 |          0.709 |
+-------------------+----------------+----------------+

```

