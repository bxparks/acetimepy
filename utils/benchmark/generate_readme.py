#!/usr/bin/python3
#
# Python script that regenerates the README.md from the embedded template. Uses
# ./generate_table.awk to regenerate the ASCII tables from the various *.txt
# files.

from subprocess import check_output

results = check_output(
    "./generate_table.awk < benchmark.txt", shell=True, text=True)

print(f"""\
# Acetz Benchmark

The `benchmark.py` script compares the speed of 4 timezone libraries:

* [acetimepy](https://github.com/bxparks/acetimepy) (AceTime for Python)
* [pytz](https://pypi.org/project/pytz/)
* [python-dateutil](https://pypi.org/project/python-dateutil/)
* [zoneinfo](https://docs.python.org/3/library/zoneinfo.html)
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

**Version**: acetimepy v0.7.0 (TZDB 2023c)

**DO NOT EDIT**: This file was auto-generated using `make README.md`.

## How to Generate

```
$ make benchmark.txt
$ make README.md
```

## Benchmarks

* Intel(R) Core(TM) i5-6300U CPU @ 2.40GHz
* Ubuntu 20.04.3 (LTS)
* Python 3.8.10

```
{results}
```
""")
