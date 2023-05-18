# AceTime for Python

This library provides the `acetime.timezone.acetz` class which is an
implementation of the
[tzinfo](https://docs.python.org/3/library/datetime.html#tzinfo-objects)
abstract class in the Python standard
[datetime](https://docs.python.org/3/library/datetime.html) package. This class
supports all timezones in the [IANA TZ
database](https://www.iana.org/time-zones), using the same algorithm used by the
`ExtendedZoneProcessor` class in the
[AceTime](https://github.com/bxparks/AceTime) C++ library for Arduino.

The default timezone database encoded in the `acetime.zonedb` subpackage
contains information for all timezones covering the all years in the IANA TZDB (
(year 1844 to 2088 as of TZDB 2023c). Custom subsets of the full TZ database
could be created to save memory using the
[AceTimeTools](https://github.com/bxparks/AceTimeTools) project but the process
has not been documented.

The `acetz` class is a subclass of `datetime.tzinfo` so it should be a drop-in
replacement for the equivalent `tzinfo` subclasses from the following
Python libraries:

* pytz (https://pypi.org/project/pytz/)
* dateutil (https://pypi.org/project/python-dateutil/)
* zoneinfo (https://docs.python.org/3/library/zoneinfo.html)

The initial motivation of this library was to provide a Python environment that
was easier to prototype compared to the embedded C++ environment required by the
[AceTime](https://github.com/bxparks/AceTime) library. That motivation became
mostly moot after [EpoxyDuino](https://github.com/bxparks/EpoxyDuino) became a
suitable environment for developing AceTime on a Linux desktop.

Currently, the main uses of this library are:

1) Generating transition buffer size requirements for the zone databases used in
   the AceTime library (since AceTime uses fixed-sized buffers instead of
   dynamically-sized buffers).
1) Validating the AceTime `ExtendedZoneProcessor` class through the
   [AceTimeValidation](https://github.com/bxparks/AceTimeValidation) project.
1) Verifying the accuracy of other Python libraries. See the [Compare to Other
   Python Libraries](#CompareToOtherLibraries) section below.
1) Exploring the feasibility of porting this library to
   [MicroPython](https://micropython.org/).

This library is intended as a research and prototype project, **not** to be used
in performance critical production environments. Informal benchmarking (see
[Benchmarks](#Benchmarks) below) shows that `acetime` is similar in performance
to `pytz` and `dateutil`, while `zoneinfo` is substantially faster than the
others because it is implemented as a C-module.

Among these 4 Python libraries that are mentioned above, `acetimepy` seems to be
the only library that returns accurate `datetime.dst()` information for all
timezones within the years supported by the IANA TZDB (from 1844 until 2088). In
addition, `acetimepy` has the advantage that the TZDB version can be controlled
deterministically, instead of being pulled from the underlying operating system
(as done by `dateutil` and `zoneinfo`). This makes `acetimepy` easier to use in
unit testing, integration testing, and in continuous integration because the
behavior of each timezone is reproducible.

This library was known as `AceTimePython` before being renamed to `acetimepy` to
be more compatible with Python package naming conventions.

**Version**: v0.7.0 (2023-05-17, TZDB 2023c)

**Changelog**: [CHANGELOG.md](CHANGELOG.md)

**See Also**:
* AceTime: https://github.com/bxparks/AceTime
* AceTimeTools: https://github.com/bxparks/AceTimeTools
* AceTimeValidation: https://github.com/bxparks/AceValidation

## Table Of Contents

* [Installation](#Installation)
* [Usage](#Usage)
    * [Package Structure](#PackageStructure)
    * [Zone Context](#ZoneContext)
    * [Acetz Using Constructor](#AcetzUsingConstructor)
    * [Acetz Using ZoneManager Factory](#AcetzUsingZoneManagerFactory)
    * [DateTime Fold](#DateTimeFold)
    * [TimeZone Is Link](#TimeZoneIsLink)
    * [TimeZone Full Name](#TimeZoneFullName)
* [Compare to Other Python Libraries](#CompareToOtherLibraries)
* [Benchmarks](#Benchmarks)
* [System Requirements](#SystemRequirements)
* [License](#License)
* [Feedback and Support](#FeedbackAndSupport)
* [Authors](#Authors)

<a name="Installation"></a>
## Installation

This library is not yet on PyPI so it needs to be installed manually from its
git repo. The library has no external dependencies other than the standard
Python library. It works on Python 3.7 or higher.

```
$ git clone https://github.com/bxparks/acetimepy
$ cd acetimepy
```

To install into your personal local environment, with symlinks back to the git
repo, you can use:

```
$ pip3 install --user -e .
```

If you are using a Python virtual environment, then you can type just:

```
$ pip3 install
```

<a name="Usage"></a>
## Usage

The package structure and usage of this library is motivated by the purpose of
this library to validate the C++ AceTime library. Therefore, this library may
not implement some "pythonic" conventions that some Python programmers may
prefer.

<a name="PackageStructure"></a>
### Package Structure

The Python naming and packaging conventions are opaque and confusing to me. Here
are some notes about this project which are hopefully helpful:

The identifier of the project on GitHub and on PyPI (TBD) is:

* `acetimepy`
    * https://github.com/bxparks/acetimepy
    * https://pypi.org/project/acetimepy (TBD)

The human-readable long version of the project is "AceTime for Python".
Both of these are intended to convey that this is the Python version of the
original [AceTime](https://github.com/bxparks/AceTime) C++ library for Arduino

The name of the top-level Python package provided by this library is:

* `acetime`

There are several modules under the `acetime` package. The end-users will
normally import 2 of them:

* `acetime.timezone`
* `acetime.zonedb`

Within the `acetime.timezone` module, there are 2 classes that the end-user will
use:

* `acetime.timezone.ZoneManager`
* `acetime.timezone.acetz` (subclass of `datetime.tzinfo`)

The `acetime.zonedb` subpackage contains various data structures which encode
the timezone information as extracted from the IANA TZDB database. (acetimepy
does *not* use the timezone files on the host computer to ensure stability and
reproducibility). There are 4 modules in the `zonedb` subpackage, but the 2 that
the end-users will likely use are:

* `acetime.zonedb.zone_infos`
    * `acetime.zonedb.zone_infos.ZONE_INFO_America_Los_Angeles`
    * `acetime.zonedb.zone_infos.ZONE_INFO_Africa_Casablanca`
    * ...
* `acetime.zonedb.zone_registry`
    * `acetime.zonedb.zone_registry.ZONE_AND_LINK_REGISTRY`
    * `acetime.zonedb.zone_registry.ZONE_REGISTRY`

The `acetime.zonedb.zone_infos.ZONE_INFO_xxx` constants are passed into the
constructor of the `acetime.timezone.acetz` object. The `ZONE_REGISTRY` and
`ZONE_AND_LINK_REGISTRY` are passed into the `acetime.timezone.ZoneManger`
object.

<a name="ZoneContext"></a>
### Zone Context

Three constants are provided in the `acetime.zonedb.zone_infos` module:

* `acetime.zonedb.zone_infos.TZDB_VERSION` (e.g. "2021e")
* `acetime.zonedb.zone_infos.START_YEAR` (e.g. 1974)
* `acetime.zonedb.zone_infos.UNTIL_YEAR` (e.g. 2100)

(These could have been placed in a separate `acetime.zonedb.zone_context`
module, but the AceTime C++ library puts them in `zone_infos`, so this library
follows that convention.)

<a name="AcetzUsingConstructor"></a>
### Acetz Using Constructor

An instance of `acetz` can be created directly through the constructor using a
`zonedb` entry, like this:

```python
from datetime import datetime
from acetime.timezone import acetz
from acetime.zonedb.zone_infos import ZONE_INFO_America_Los_Angeles

# Create an acetz from a zonedb entry.
tz = acetz(ZONE_INFO_America_Los_Angeles)

# Create date from unix seconds
unix_seconds = 954669600
dte = datetime.fromtimestamp(unix_seconds, tz=tz)

# Create date from components
dtc = datetime(2000, 4, 2, 3, 0, 0, tzinfo=tz)

assert dte == dtc
print(dte)
```

This should print
```
2000-04-02 03:00:00-07:00
```

The list of other `ZONE_INFO_xxx` entries can be found in the
[zone_infos.py](src/acetime/zonedb/zone_infos.py) file.

<a name="AcetzUsingZoneManagerFactory"></a>
### Acetz Using ZoneManager Factory

The `acetz` class can also be created through the `ZoneManager` factory class.
An instance of `ZoneManager` must be configured with the registry of the
supported timezones. This library provides an `acetime.zonedb.zone_registry`
module which has 2 pre-generated registries containing timezone information from
1974 until 2100:

* `acetime.zonedb.zone_registry.ZONE_REGISTRY`
    * contains all primary Zone entries
    * 377 zones as of TZDB 2021e
* `acetime.zonedb.zone_registry.ZONE_AND_LINK_REGISTRY`
    * contains all Zone and Link entries
    * 594 zones and links as of TZDB 2021e

We can then create an instance of `acetz` using a timezone name (e.g.
"America/Los_Angeles") through the `ZoneManager.gettz()` method:

```Python
from datetime import datetime
from acetime.acetz import ZoneManager
from acetime.zonedb.zone_registry import ZONE_REGISTRY
from acetime.common import SECONDS_SINCE_UNIX_EPOCH

# Create a ZoneManager configured with the given registry
zone_manager = ZoneManager(ZONE_REGISTRY)

# Create an acetz using the ZoneManager.
tz = zone_manager.gettz('America/Los_Angeles')

# Create date from epoch seconds
acetime_seconds = 7984800
unix_seconds = acetime_seconds + SECONDS_SINCE_UNIX_EPOCH
dte = datetime.fromtimestamp(unix_seconds, tz=tz)

# Create date from components
dtc = datetime(2000, 4, 2, 3, 0, 0, tzinfo=tz)

assert dte == dtc
print(dte)
```

This should also print
```
2000-04-02 03:00:00-07:00
```

It is possible to generate custom registries with different subsets of timezones
using the tools provided by the
[AceTimeTools](https://github.com/bxparks/AceTimeTools) project.

<a name="DateTimeFold"></a>
### DateTime Fold

The `acetz` class supports the `fold` parameter in
[`datetime`](https://docs.python.org/3/library/datetime.html#datetime-objects)
which was introduced in Python 3.6.

The following code snippet shows 2 ways to create a `datetime` for 01:59:59
which occurs twice on 2000-10-29 in the America/Los_Angeles timezone:

```python
from datetime import datetime
from acetime.acetz import acetz
from acetime.zonedb.zone_infos import ZONE_INFO_America_Los_Angeles

tz = acetz(ZONE_INFO_America_Los_Angeles)

# Creates the earlier of the 2 times.
dt = datetime(2000, 10, 29, 1, 59, 59, tzinfo=tz, fold=0)
print(dt)

# Creates the later of the 2 times.
dt = datetime(2000, 10, 29, 1, 59, 59, tzinfo=tz, fold=1)
print(dt)
```

This prints:
```
2000-10-29 01:59:59-07:00
2000-10-29 01:59:59-08:00
```

<a name="TimeZoneIsLink"></a>
### TimeZone Is Link

The `acetz` class extends the `tzinfo` class with the `islink()` method that
returns `True` if the timezone is a Link entry instead of a Zone entry:

```Python
class acetz(tzinfo):
    ...
    def islink(self) -> bool:
    ...
```

<a name="TimeZoneFullName"></a>
### TimeZone Full Name

The `acetz` class extends the `tzinfo` class with the `tzfullname()` method that
complements the `tzname()` method from `tzinfo`:

```Python
class acetz(tzinfo):
    ...
    def tzfullname(self, follow_link: bool = False) -> str:
    ...
```

For normal Zone entries, this returns the full time zone name (e.g.
`America/Los_Angeles`). For Link entries, this returns the name of the link
(e.g. `US/Pacific`). If the `follow_link` parameter is set to `True`, the method
returns the name of the target time zone (i.e. `America/Los_Angeles`).

<a name="CompareToOtherLibraries"></a>
## Compare to Other Python Libraries

The [report_zoneinfo.py](utils/Variance/report_zoneinfo.py) script compares the
`acetime.timezone.acetz` class against the Python 3.9 `zoneinfo.ZoneInfo` class,
and generates a variance report. The output
[zoneinfo_variance.txt](utils/Variance/zoneinfo_variance.txt) is reproduced
below. It shows that the `zoneinfo.ZoneInfo` class has some bugs related to the
accuracy of the `datetime.dst()` method for a few zones. It is relatively easy
to see that `acetime.timezone.acetz` produces the correct DST offset by going to
the [original TZDB source files](https://github.com/eggert/tz) for each zone.

```
# Variance report for acetime.timezone.acetz compared to Python 3.9
# zoneinfo.ZoneInfo.
#
# Context
# -------
# Acetimepy Version: 0.4.0
# Acetimepy ZoneDB Version: 2021e
# Acetimepy ZoneDB Start Year: 1974
# Acetimepy ZoneDB Until Year: 2050
# Zoneinfo Version: Python 3.9 2021e
# Report Start Year: 1974
# Report Until Year: 2050
#
# Report Format
# -------------
# Zone {zone_name}
# {seconds}: {date}: {label}: exp {value}, obs {value}
# [...]

Zone America/Bahia_Banderas
1270371600: 2010-04-04 04:00:00-05:00: dst_offset: exp 3600, obs 7200
1288508340: 2010-10-31 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1301817600: 2011-04-03 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1319957940: 2011-10-30 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1333267200: 2012-04-01 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1351407540: 2012-10-28 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1365321600: 2013-04-07 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1382857140: 2013-10-27 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1396771200: 2014-04-06 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1414306740: 2014-10-26 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1428220800: 2015-04-05 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1445756340: 2015-10-25 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1459670400: 2016-04-03 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1477810740: 2016-10-30 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1491120000: 2017-04-02 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1509260340: 2017-10-29 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1522569600: 2018-04-01 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1540709940: 2018-10-28 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1554624000: 2019-04-07 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1572159540: 2019-10-27 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1586073600: 2020-04-05 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1603609140: 2020-10-25 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1617523200: 2021-04-04 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1635663540: 2021-10-31 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1648972800: 2022-04-03 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1667113140: 2022-10-30 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1680422400: 2023-04-02 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1698562740: 2023-10-29 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1712476800: 2024-04-07 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1730012340: 2024-10-27 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1743926400: 2025-04-06 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1761461940: 2025-10-26 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1775376000: 2026-04-05 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1792911540: 2026-10-25 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1806825600: 2027-04-04 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1824965940: 2027-10-31 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1838275200: 2028-04-02 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1856415540: 2028-10-29 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1869724800: 2029-04-01 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1887865140: 2029-10-28 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1901779200: 2030-04-07 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1919314740: 2030-10-27 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1933228800: 2031-04-06 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1950764340: 2031-10-26 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1964678400: 2032-04-04 03:00:00-05:00: dst_offset: exp 3600, obs 7200
1982818740: 2032-10-31 01:59:00-05:00: dst_offset: exp 3600, obs 7200
1996128000: 2033-04-03 03:00:00-05:00: dst_offset: exp 3600, obs 7200
2014268340: 2033-10-30 01:59:00-05:00: dst_offset: exp 3600, obs 7200
2027577600: 2034-04-02 03:00:00-05:00: dst_offset: exp 3600, obs 7200
2045717940: 2034-10-29 01:59:00-05:00: dst_offset: exp 3600, obs 7200
2059027200: 2035-04-01 03:00:00-05:00: dst_offset: exp 3600, obs 7200
2077167540: 2035-10-28 01:59:00-05:00: dst_offset: exp 3600, obs 7200
2091081600: 2036-04-06 03:00:00-05:00: dst_offset: exp 3600, obs 7200
2108617140: 2036-10-26 01:59:00-05:00: dst_offset: exp 3600, obs 7200
2122531200: 2037-04-05 03:00:00-05:00: dst_offset: exp 3600, obs 7200
2140066740: 2037-10-25 01:59:00-05:00: dst_offset: exp 3600, obs 7200
Zone America/Scoresbysund
354679200: 1981-03-29 02:00:00+00:00: dst_offset: exp 3600, obs 7200
370400340: 1981-09-27 00:59:00+00:00: dst_offset: exp 3600, obs 7200
Zone Asia/Choibalsan
417974400: 1983-04-01 02:00:00+10:00: dst_offset: exp 3600, obs 7200
433778340: 1983-09-30 23:59:00+10:00: dst_offset: exp 3600, obs 7200
449593200: 1984-04-01 01:00:00+10:00: dst_offset: exp 3600, obs 7200
465314340: 1984-09-29 23:59:00+10:00: dst_offset: exp 3600, obs 7200
481042800: 1985-03-31 01:00:00+10:00: dst_offset: exp 3600, obs 7200
496763940: 1985-09-28 23:59:00+10:00: dst_offset: exp 3600, obs 7200
512492400: 1986-03-30 01:00:00+10:00: dst_offset: exp 3600, obs 7200
528213540: 1986-09-27 23:59:00+10:00: dst_offset: exp 3600, obs 7200
543942000: 1987-03-29 01:00:00+10:00: dst_offset: exp 3600, obs 7200
559663140: 1987-09-26 23:59:00+10:00: dst_offset: exp 3600, obs 7200
575391600: 1988-03-27 01:00:00+10:00: dst_offset: exp 3600, obs 7200
591112740: 1988-09-24 23:59:00+10:00: dst_offset: exp 3600, obs 7200
606841200: 1989-03-26 01:00:00+10:00: dst_offset: exp 3600, obs 7200
622562340: 1989-09-23 23:59:00+10:00: dst_offset: exp 3600, obs 7200
638290800: 1990-03-25 01:00:00+10:00: dst_offset: exp 3600, obs 7200
654616740: 1990-09-29 23:59:00+10:00: dst_offset: exp 3600, obs 7200
670345200: 1991-03-31 01:00:00+10:00: dst_offset: exp 3600, obs 7200
686066340: 1991-09-28 23:59:00+10:00: dst_offset: exp 3600, obs 7200
701794800: 1992-03-29 01:00:00+10:00: dst_offset: exp 3600, obs 7200
717515940: 1992-09-26 23:59:00+10:00: dst_offset: exp 3600, obs 7200
733244400: 1993-03-28 01:00:00+10:00: dst_offset: exp 3600, obs 7200
748965540: 1993-09-25 23:59:00+10:00: dst_offset: exp 3600, obs 7200
764694000: 1994-03-27 01:00:00+10:00: dst_offset: exp 3600, obs 7200
780415140: 1994-09-24 23:59:00+10:00: dst_offset: exp 3600, obs 7200
796143600: 1995-03-26 01:00:00+10:00: dst_offset: exp 3600, obs 7200
811864740: 1995-09-23 23:59:00+10:00: dst_offset: exp 3600, obs 7200
828198000: 1996-03-31 01:00:00+10:00: dst_offset: exp 3600, obs 7200
843919140: 1996-09-28 23:59:00+10:00: dst_offset: exp 3600, obs 7200
859647600: 1997-03-30 01:00:00+10:00: dst_offset: exp 3600, obs 7200
875368740: 1997-09-27 23:59:00+10:00: dst_offset: exp 3600, obs 7200
891097200: 1998-03-29 01:00:00+10:00: dst_offset: exp 3600, obs 7200
906818340: 1998-09-26 23:59:00+10:00: dst_offset: exp 3600, obs 7200
988390800: 2001-04-28 03:00:00+10:00: dst_offset: exp 3600, obs 7200
1001692740: 2001-09-29 01:59:00+10:00: dst_offset: exp 3600, obs 7200
1017421200: 2002-03-30 03:00:00+10:00: dst_offset: exp 3600, obs 7200
1033142340: 2002-09-28 01:59:00+10:00: dst_offset: exp 3600, obs 7200
1048870800: 2003-03-29 03:00:00+10:00: dst_offset: exp 3600, obs 7200
1064591940: 2003-09-27 01:59:00+10:00: dst_offset: exp 3600, obs 7200
1080320400: 2004-03-27 03:00:00+10:00: dst_offset: exp 3600, obs 7200
1096041540: 2004-09-25 01:59:00+10:00: dst_offset: exp 3600, obs 7200
1111770000: 2005-03-26 03:00:00+10:00: dst_offset: exp 3600, obs 7200
1127491140: 2005-09-24 01:59:00+10:00: dst_offset: exp 3600, obs 7200
1143219600: 2006-03-25 03:00:00+10:00: dst_offset: exp 3600, obs 7200
1159545540: 2006-09-30 01:59:00+10:00: dst_offset: exp 3600, obs 7200
Zone Asia/Ust-Nera
354898800: 1981-04-01 03:00:00+12:00: dst_offset: exp 3600, obs 10800
370699140: 1981-09-30 23:59:00+12:00: dst_offset: exp 3600, obs 10800
386427600: 1982-04-01 01:00:00+12:00: dst_offset: exp 3600, obs 10800
402235140: 1982-09-30 23:59:00+12:00: dst_offset: exp 3600, obs 10800
417963600: 1983-04-01 01:00:00+12:00: dst_offset: exp 3600, obs 10800
433771140: 1983-09-30 23:59:00+12:00: dst_offset: exp 3600, obs 10800
449586000: 1984-04-01 01:00:00+12:00: dst_offset: exp 3600, obs 10800
465317940: 1984-09-30 02:59:00+12:00: dst_offset: exp 3600, obs 10800
Zone Pacific/Rarotonga
279714600: 1978-11-12 01:00:00-09:30: dst_offset: exp 1800, obs 3600
289387740: 1979-03-03 23:59:00-09:30: dst_offset: exp 1800, obs 3600
309952800: 1979-10-28 00:30:00-09:30: dst_offset: exp 1800, obs 3600
320837340: 1980-03-01 23:59:00-09:30: dst_offset: exp 1800, obs 3600
341402400: 1980-10-26 00:30:00-09:30: dst_offset: exp 1800, obs 3600
352286940: 1981-02-28 23:59:00-09:30: dst_offset: exp 1800, obs 3600
372852000: 1981-10-25 00:30:00-09:30: dst_offset: exp 1800, obs 3600
384341340: 1982-03-06 23:59:00-09:30: dst_offset: exp 1800, obs 3600
404906400: 1982-10-31 00:30:00-09:30: dst_offset: exp 1800, obs 3600
415790940: 1983-03-05 23:59:00-09:30: dst_offset: exp 1800, obs 3600
436356000: 1983-10-30 00:30:00-09:30: dst_offset: exp 1800, obs 3600
447240540: 1984-03-03 23:59:00-09:30: dst_offset: exp 1800, obs 3600
467805600: 1984-10-28 00:30:00-09:30: dst_offset: exp 1800, obs 3600
478690140: 1985-03-02 23:59:00-09:30: dst_offset: exp 1800, obs 3600
499255200: 1985-10-27 00:30:00-09:30: dst_offset: exp 1800, obs 3600
510139740: 1986-03-01 23:59:00-09:30: dst_offset: exp 1800, obs 3600
530704800: 1986-10-26 00:30:00-09:30: dst_offset: exp 1800, obs 3600
541589340: 1987-02-28 23:59:00-09:30: dst_offset: exp 1800, obs 3600
562154400: 1987-10-25 00:30:00-09:30: dst_offset: exp 1800, obs 3600
573643740: 1988-03-05 23:59:00-09:30: dst_offset: exp 1800, obs 3600
594208800: 1988-10-30 00:30:00-09:30: dst_offset: exp 1800, obs 3600
605093340: 1989-03-04 23:59:00-09:30: dst_offset: exp 1800, obs 3600
625658400: 1989-10-29 00:30:00-09:30: dst_offset: exp 1800, obs 3600
636542940: 1990-03-03 23:59:00-09:30: dst_offset: exp 1800, obs 3600
657108000: 1990-10-28 00:30:00-09:30: dst_offset: exp 1800, obs 3600
667992540: 1991-03-02 23:59:00-09:30: dst_offset: exp 1800, obs 3600
```

<a name="Benchmarks"></a>
## Benchmarks

The [utils/AcetzBenchmark](utils/AcetzBenchmark) script is an informal
benchmarking of 4 Python timezone libraries: `acetime`, `pytz`, `dateutil` and
`zoneinfo`. The results are:

```
+-------------------+----------------+----------------+
| Time Zone Library | comp to epoch  | epoch to comp  |
|                   | (micros/iter)  | (micros/iter)  |
|-------------------+----------------+----------------|
| acetime           |         10.256 |         12.700 |
| dateutil          |          5.974 |          7.372 |
| pytz              |         15.744 |         15.286 |
| zoneinfo          |          1.415 |          0.636 |
+-------------------+----------------+----------------+
```

<a name="SystemRequirements"></a>
## System Requirements

For end-users of the library:

* Python 3.7 or newer

To generate the `zonedb` TZ database:

* [AceTimeTools](https://github.com/bxparks/AceTimeTools)

To run the validation tests:

* [AceTimeValidation](https://github.com/bxparks/AceTimeValidation)

<a name="License"></a>
## License

[MIT License](https://opensource.org/licenses/MIT)

<a name="FeedbackAndSupport"></a>
## Feedback and Support

If you have any questions, comments, or feature requests for this library,
please use the [GitHub
Discussions](https://github.com/bxparks/acetimepy/discussions) for this
project. If you have bug reports, please file a ticket in [GitHub
Issues](https://github.com/bxparks/acetimepy/issues). Feature requests
should go into Discussions first because they often have alternative solutions
which are useful to remain visible, instead of disappearing from the default
view of the Issue tracker after the ticket is closed.

Please refrain from emailing me directly unless the content is sensitive. The
problem with email is that I cannot reference the email conversation when other
people ask similar questions later.

<a name="Authors"></a>
## Authors

* Created by Brian T. Park (brian@xparks.net).
