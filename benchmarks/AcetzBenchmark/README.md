# Acetz Benchmark

The `benchmark.py` compares the speed of 4 timezone subclasses of `tzinfo`:

* `acetz` from AceTimePython projet
* `dateutil.tz` from the `python-dateutil` project
* `pytz` from the `pytz` project
* `zoneinfo` from the Python 3.9 standard library

There are 2 columns for each library:

* "comp to epoch": Measures the time to convert date-time components (yyyy-mm-dd
  hh:mm:ss) to epoch seconds.
* "epoch to comp": Measures the reverse mapping, from epoch seconds to date-time
  components.

The `benchmark.py` scans through all 377 timezones, sampling 2 days, for each
month, from the year 2000 until 2037. The number in the table below is given
units of microseconds per iteration, averaged over all timezones.

**Version**: AceTimePython v1.0.2+

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
|-------------------+----------------+----------------|
| acetz             |         10.256 |         12.700 |
| dateutil          |          5.974 |          7.372 |
| pytz              |         15.744 |         15.286 |
| zoneinfo          |          1.415 |          0.636 |
+-------------------+----------------+----------------+

```

