# AceTime for Python

The `acetimepy` library provides classes compatible with the Python standard
[datetime](https://docs.python.org/3/library/datetime.html) library to support
all timezones defined by the [IANA TZ
database](https://www.iana.org/time-zones). In particular, the
`acetime.timezone.acetz` class is an implementation of the
[tzinfo](https://docs.python.org/3/library/datetime.html#tzinfo-objects)
abstract class, and is a drop-in replacement for timezone classes provided by
other Python libraries such as:

* pytz (https://pypi.org/project/pytz/)
* dateutil (https://pypi.org/project/python-dateutil/)
* zoneinfo (https://docs.python.org/3/library/zoneinfo.html)

The initial motivation of this library was to build a Python environment that
was easier to prototype compared to the embedded C++ environment required by the
[AceTime](https://github.com/bxparks/AceTime) library. To support that use-case,
the `acetz` class uses the same algorithm used by the `ExtendedZoneProcessor`
class in the [AceTime](https://github.com/bxparks/AceTime) C++ library for
Arduino. That motivation became mostly moot after
[EpoxyDuino](https://github.com/bxparks/EpoxyDuino) became a suitable and
productive environment for developing AceTime on a Linux desktop.

There are 2 timezone databases provided by this library:

* `acetime.zonedb`
    * contains rules and transitions only from the year 2000 and onwards
    * matches the `zonedb` and `zonedbx` databases in the AceTime library
* `acetime.zonedball`
    * contains rules and transitions for all years defined by the IANA
      TZDB, currently from 1844 onwards.
    * useful for validating against third-party libraries

Custom subsets of the full TZ database could be created to save memory using the
[AceTimeSuite/compiler](https://github.com/bxparks/AceTimeSuite) compiler. The
process has not been documented, but can probably be inferred from the
`Makefile`s in [acetime.zonedb](src/acetime/zonedb) and
[acetime.zonedball](src/acetime/zonedball).

Currently, the main uses of this library are:

1) Generating transition buffer size requirements for the zone databases used in
   the AceTime library (since AceTime uses fixed-sized buffers instead of
   dynamically-sized buffers).
1) Validating the AceTime `ExtendedZoneProcessor` class through the `validation`
   directory of the [AceTimeSuite](https://github.com/bxparks/AceTimeSuite)
   project.
1) Verifying the accuracy of other Python libraries. See the [Compare to Other
   Python Libraries](#CompareToOtherLibraries) section below.
1) Exploring the feasibility of porting this library to
   [MicroPython](https://micropython.org/).

This library is intended as a reference implementation, with priority given to
accuracy, ease of maintenance, and compatibility with the AceTime library for
Arduino. It has not been optimized for speed or memory efficiency, so it is
**not** intended to be used in critical production environments. Informal
benchmarking (see [Benchmarks](#Benchmarks) below) shows that `acetimepy` is
similar in performance to `pytz` and `dateutil`, while `zoneinfo` is
substantially faster than the others because it is implemented as a C-module.

Among these 4 Python libraries that are mentioned above, `acetimepy` seems to be
the only library that calculates accurate `datetime.dst()` information for all
timezones within the years supported by the IANA TZDB (from 1844 until 2088). In
addition, `acetimepy` has the advantage that the TZDB version can be controlled
deterministically, instead of being pulled from the underlying operating system
(as done by `dateutil` and `zoneinfo`). This makes `acetimepy` easier to use for
unit testing, integration testing, and continuous integration because the
behavior of each timezone is reproducible.

This library was known as `AceTimePython` before being renamed to `acetimepy` to
be more compatible with Python package naming conventions.

**Version**: 0.9.0 (2025-04-25, TZDB 2025b)

**Changelog**: [CHANGELOG.md](CHANGELOG.md)

**See Also**:
* AceTimeSuite: https://github.com/bxparks/AceTimeSuite
* AceTime: https://github.com/bxparks/AceTime

## Table Of Contents

* [Installation](#Installation)
* [Usage](#Usage)
    * [Package Structure](#PackageStructure)
    * [Zone Context](#ZoneContext)
    * [Acetz Using Constructor](#AcetzUsingConstructor)
    * [Acetz Using ZoneManager Factory](#AcetzUsingZoneManagerFactory)
    * [DateTime Fold](#DateTimeFold)
    * [TimeZone Full Name](#TimeZoneFullName)
    * [TimeZone Is Link](#TimeZoneIsLink)
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
normally import 3 of them:

* `acetime.timezone`
* `acetime.zonedb`
* `acetime.zonedball`

Within the `acetime.timezone` module, there are 2 classes that the end-user will
use:

* `acetime.timezone.ZoneManager`
* `acetime.timezone.acetz` (subclass of `datetime.tzinfo`)

The `zonedb` and `zonedball` subpackages contain various data structures which
encode the timezone information as extracted from the IANA TZDB database.
(acetimepy does *not* use the timezone files on the host computer to ensure
stability and reproducibility). There are 4 modules in each of the subpackages,
but the 2 that the end-users will likely use are:

* `zonedb*.zone_infos`
    * `zonedb*.zone_infos.ZONE_INFO_America_Los_Angeles`
    * `zonedb*.zone_infos.ZONE_INFO_Africa_Casablanca`
    * ...
* `zonedb*.zone_registry`
    * `zonedb*.zone_registry.ZONE_AND_LINK_REGISTRY`
    * `zonedb*.zone_registry.ZONE_REGISTRY`

The `zonedb*.zone_infos.ZONE_INFO_xxx` constants are passed into the
constructor of the `acetime.timezone.acetz` object. The `ZONE_REGISTRY` and
`ZONE_AND_LINK_REGISTRY` are passed into the `acetime.timezone.ZoneManger`
object.

The `ZONE_REGISTRY` contains only the Zone entries (350 as of TZDB 2023c). This
is a shorter list that is useful for unit and integration tests.

The `ZONE_AND_LINK_REGISTRY` contains both Zone and Link entries (596 as of
2023c). This should be used if the application is user-facing because it will
contain all the timezones that the end-user is allowed to use.

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
    * 350 zones as of TZDB 2023c
    * useful for unit and integration tests
* `acetime.zonedb.zone_registry.ZONE_AND_LINK_REGISTRY`
    * contains all Zone and Link entries
    * 596 zones and links as of TZDB 2023c
    * use this for user-facing applications

We can then create an instance of `acetz` using a timezone name (e.g.
"America/Los_Angeles") through the `ZoneManager.gettz()` method:

```Python
from datetime import datetime
from acetime.acetz import ZoneManager
from acetime.zonedb.zone_registry import ZONE_AND_LINK_REGISTRY

# Create a ZoneManager configured with the given registry
zone_manager = ZoneManager(ZONE_AND_LINK_REGISTRY)

# Create an acetz using the ZoneManager.
tz = zone_manager.gettz('America/Los_Angeles')

# Create date from unix seconds
# $ date +%s -d '2000-04-02T03:00:00-07:00'
unix_seconds = 954669600
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
[AceTimeSuite/compiler](https://github.com/bxparks/AceTimeSuite) tool.

<a name="DateTimeFold"></a>
### DateTime Fold

The `acetz` class supports the `fold` parameter in
[`datetime`](https://docs.python.org/3/library/datetime.html#datetime-objects)
which is described in [PEP 495](https://peps.python.org/pep-0495/) and
implemented in in Python 3.6.

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

<a name="TimeZoneFullName"></a>
### TimeZone Full Name

The `acetz` class extends the `tzinfo` class with the `tzfullname()` method that
complements the `tzname()` method from `tzinfo`:

```Python
class acetz(tzinfo):
    ...
    def tzfullname(self) -> str:
    ...
```

For normal Zone entries, this returns the full time zone name (e.g.
`America/Los_Angeles`). For Link entries, this returns the name of the link
(e.g. `US/Pacific`).

<a name="TimeZoneIsLink"></a>
### TimeZone Is Link

The `acetz` class adds 2 methods in addition to the inherited methods from the
`tzinfo` base class to support Link entries. The `islink()` method
returns `True` for Links, and the `targetname()` returns the name of the target
Zone:

```Python
class acetz(tzinfo):
    ...
    def islink(self) -> bool:
    def targetname(self) -> str:
    ...
```

The `targetname()` method returns the empty string for normal Zone entries.

<a name="CompareToOtherLibraries"></a>
## Compare to Other Python Libraries

The [validate_zoneinfo](utils/validate_zoneinfo) directory compares the
`acetime.timezone.acetz` class against the Python 3.9 `zoneinfo.ZoneInfo` class,
and generates a variance report. The output
[zoneinfo_variance.txt](utils/validate_zoneinfo/zoneinfo_variance.txt) is
reproduced below. It shows that the `zoneinfo.ZoneInfo` class has some bugs
related to the accuracy of the `datetime.dst()` method for a few zones. It is
usually easy to see that `acetime.timezone.acetz` produces the correct DST
offset by going to the raw [TZDB](https://github.com/eggert/tz) source
files for each zone.

```
# Variance report for acetime.timezone.acetz compared to Python 3.10
# zoneinfo.ZoneInfo.
#
# Context
# -------
# Acetimepy Version: 0.7.0
# Acetimepy ZoneDB Version: 2023c
# Acetimepy ZoneDB Start Year: 1800
# Acetimepy ZoneDB Until Year: 10000
# Python Version: 3.10.6 (main, Mar 10 2023, 10:55:28) [GCC 11.3.0]
# ZoneInfo Version: 2022c
# Report Start Year: 1840
# Report Until Year: 2100
#
# Report Format
# -------------
# Zone {zone_name}
# {seconds}: {date}: {label}: exp {value}, obs {value}
# [...]

Zone America/Bahia_Banderas
1270371600: 2010-04-04 04:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1288508340: 2010-10-31 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1301817600: 2011-04-03 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1319957940: 2011-10-30 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1333267200: 2012-04-01 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1351407540: 2012-10-28 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1365321600: 2013-04-07 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1382857140: 2013-10-27 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1396771200: 2014-04-06 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1414306740: 2014-10-26 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1428220800: 2015-04-05 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1445756340: 2015-10-25 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1459670400: 2016-04-03 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1477810740: 2016-10-30 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1491120000: 2017-04-02 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1509260340: 2017-10-29 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1522569600: 2018-04-01 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1540709940: 2018-10-28 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1554624000: 2019-04-07 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1572159540: 2019-10-27 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1586073600: 2020-04-05 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1603609140: 2020-10-25 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1617523200: 2021-04-04 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1635663540: 2021-10-31 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1648972800: 2022-04-03 03:00:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
1667113140: 2022-10-30 01:59:00-05:00: dst_offset: acetz 3600; zoneinfo 7200
Zone America/Indiana/Tell_City
-21484800: 1969-04-27 04:00:00-04:00: dst_offset: acetz 3600; zoneinfo 7200
-5767260: 1969-10-26 01:59:00-04:00: dst_offset: acetz 3600; zoneinfo 7200
9961200: 1970-04-26 03:00:00-04:00: dst_offset: acetz 3600; zoneinfo 7200
25682340: 1970-10-25 01:59:00-04:00: dst_offset: acetz 3600; zoneinfo 7200
Zone America/Inuvik
294228000: 1979-04-29 04:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
309945540: 1979-10-28 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
325674000: 1980-04-27 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
341395140: 1980-10-26 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
357123600: 1981-04-26 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
372844740: 1981-10-25 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
388573200: 1982-04-25 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
404899140: 1982-10-31 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
420022800: 1983-04-24 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
436348740: 1983-10-30 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
452077200: 1984-04-29 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
467798340: 1984-10-28 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
483526800: 1985-04-28 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
499247940: 1985-10-27 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
514976400: 1986-04-27 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
530697540: 1986-10-26 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
544611600: 1987-04-05 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
562147140: 1987-10-25 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
576061200: 1988-04-03 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
594201540: 1988-10-30 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
607510800: 1989-04-02 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
625651140: 1989-10-29 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
638960400: 1990-04-01 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
657100740: 1990-10-28 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
671014800: 1991-04-07 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
688550340: 1991-10-27 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
702464400: 1992-04-05 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
719999940: 1992-10-25 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
733914000: 1993-04-04 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
752054340: 1993-10-31 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
765363600: 1994-04-03 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
783503940: 1994-10-30 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
796813200: 1995-04-02 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
814953540: 1995-10-29 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
828867600: 1996-04-07 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
846403140: 1996-10-27 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
860317200: 1997-04-06 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
877852740: 1997-10-26 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
891766800: 1998-04-05 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
909302340: 1998-10-25 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
923216400: 1999-04-04 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
941356740: 1999-10-31 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
954666000: 2000-04-02 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
972806340: 2000-10-29 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
986115600: 2001-04-01 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1004255940: 2001-10-28 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1018170000: 2002-04-07 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1035705540: 2002-10-27 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1049619600: 2003-04-06 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1067155140: 2003-10-26 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1081069200: 2004-04-04 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1099209540: 2004-10-31 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1112518800: 2005-04-03 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1130659140: 2005-10-30 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1143968400: 2006-04-02 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1162108740: 2006-10-29 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1173603600: 2007-03-11 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1194163140: 2007-11-04 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1205053200: 2008-03-09 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1225612740: 2008-11-02 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1236502800: 2009-03-08 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1257062340: 2009-11-01 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1268557200: 2010-03-14 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1289116740: 2010-11-07 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1300006800: 2011-03-13 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1320566340: 2011-11-06 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1331456400: 2012-03-11 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1352015940: 2012-11-04 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1362906000: 2013-03-10 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1383465540: 2013-11-03 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1394355600: 2014-03-09 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1414915140: 2014-11-02 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1425805200: 2015-03-08 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1446364740: 2015-11-01 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1457859600: 2016-03-13 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1478419140: 2016-11-06 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1489309200: 2017-03-12 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1509868740: 2017-11-05 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1520758800: 2018-03-11 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1541318340: 2018-11-04 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1552208400: 2019-03-10 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1572767940: 2019-11-03 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1583658000: 2020-03-08 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1604217540: 2020-11-01 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1615712400: 2021-03-14 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1636271940: 2021-11-07 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1647162000: 2022-03-13 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1667721540: 2022-11-06 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1678611600: 2023-03-12 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1699171140: 2023-11-05 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1710061200: 2024-03-10 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1730620740: 2024-11-03 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1741510800: 2025-03-09 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1762070340: 2025-11-02 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1772960400: 2026-03-08 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1793519940: 2026-11-01 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1805014800: 2027-03-14 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1825574340: 2027-11-07 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1836464400: 2028-03-12 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1857023940: 2028-11-05 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1867914000: 2029-03-11 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1888473540: 2029-11-04 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1899363600: 2030-03-10 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1919923140: 2030-11-03 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1930813200: 2031-03-09 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1951372740: 2031-11-02 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1962867600: 2032-03-14 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1983427140: 2032-11-07 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
1994317200: 2033-03-13 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
2014876740: 2033-11-06 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
2025766800: 2034-03-12 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
2046326340: 2034-11-05 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
2057216400: 2035-03-11 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
2077775940: 2035-11-04 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
2088666000: 2036-03-09 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
2109225540: 2036-11-02 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
2120115600: 2037-03-08 03:00:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
2140675140: 2037-11-01 01:59:00-06:00: dst_offset: acetz 3600; zoneinfo 7200
Zone America/Montevideo
-1459627200: 1923-10-01 01:00:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1443819660: 1924-03-31 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1428006600: 1924-10-01 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1412283660: 1925-03-31 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1396470600: 1925-10-01 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1380747660: 1926-03-31 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1141590600: 1933-10-29 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1128286860: 1934-03-31 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1110141000: 1934-10-28 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1096837260: 1935-03-30 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1078691400: 1935-10-27 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1065387660: 1936-03-28 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1047241800: 1936-10-25 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1033938060: 1937-03-27 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1015187400: 1937-10-31 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-1002488460: 1938-03-26 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-983737800: 1938-10-30 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-971038860: 1939-03-25 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-954707400: 1939-10-01 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-938984460: 1940-03-30 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-920838600: 1940-10-27 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-907534860: 1941-03-29 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-896819400: 1941-08-01 00:30:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
-853621260: 1942-12-13 23:59:00-03:00: dst_offset: acetz 1800; zoneinfo 3600
Zone America/Punta_Arenas
-1335986220: 1927-09-01 00:43:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1317585660: 1928-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1304362800: 1928-09-01 01:00:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1286049660: 1929-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1272826800: 1929-09-01 01:00:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1254513660: 1930-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1241290800: 1930-09-01 01:00:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1222977660: 1931-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1209754800: 1931-09-01 01:00:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1191355260: 1932-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-736632000: 1946-08-29 00:00:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-718056060: 1947-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
Zone America/Santiago
-1335986220: 1927-09-01 00:43:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1317585660: 1928-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1304362800: 1928-09-01 01:00:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1286049660: 1929-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1272826800: 1929-09-01 01:00:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1254513660: 1930-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1241290800: 1930-09-01 01:00:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1222977660: 1931-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1209754800: 1931-09-01 01:00:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-1191355260: 1932-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-736635600: 1946-08-28 23:00:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
-718056060: 1947-03-31 23:59:00-04:00: dst_offset: acetz 3600; zoneinfo 2565
Zone America/Scoresbysund
354679200: 1981-03-29 02:00:00+00:00: dst_offset: acetz 3600; zoneinfo 7200
370400340: 1981-09-27 00:59:00+00:00: dst_offset: acetz 3600; zoneinfo 7200
Zone Asia/Choibalsan
417974400: 1983-04-01 02:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
433778340: 1983-09-30 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
449593200: 1984-04-01 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
465314340: 1984-09-29 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
481042800: 1985-03-31 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
496763940: 1985-09-28 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
512492400: 1986-03-30 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
528213540: 1986-09-27 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
543942000: 1987-03-29 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
559663140: 1987-09-26 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
575391600: 1988-03-27 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
591112740: 1988-09-24 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
606841200: 1989-03-26 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
622562340: 1989-09-23 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
638290800: 1990-03-25 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
654616740: 1990-09-29 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
670345200: 1991-03-31 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
686066340: 1991-09-28 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
701794800: 1992-03-29 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
717515940: 1992-09-26 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
733244400: 1993-03-28 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
748965540: 1993-09-25 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
764694000: 1994-03-27 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
780415140: 1994-09-24 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
796143600: 1995-03-26 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
811864740: 1995-09-23 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
828198000: 1996-03-31 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
843919140: 1996-09-28 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
859647600: 1997-03-30 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
875368740: 1997-09-27 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
891097200: 1998-03-29 01:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
906818340: 1998-09-26 23:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
988390800: 2001-04-28 03:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1001692740: 2001-09-29 01:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1017421200: 2002-03-30 03:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1033142340: 2002-09-28 01:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1048870800: 2003-03-29 03:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1064591940: 2003-09-27 01:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1080320400: 2004-03-27 03:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1096041540: 2004-09-25 01:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1111770000: 2005-03-26 03:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1127491140: 2005-09-24 01:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1143219600: 2006-03-25 03:00:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
1159545540: 2006-09-30 01:59:00+10:00: dst_offset: acetz 3600; zoneinfo 7200
Zone Asia/Hong_Kong
-891579600: 1941-10-01 03:30:00+08:30: dst_offset: acetz 1800; zoneinfo -1800
-884248260: 1941-12-24 23:59:00+08:30: dst_offset: acetz 1800; zoneinfo -1800
Zone Asia/Ust-Nera
354898800: 1981-04-01 03:00:00+12:00: dst_offset: acetz 3600; zoneinfo 10800
370699140: 1981-09-30 23:59:00+12:00: dst_offset: acetz 3600; zoneinfo 10800
386427600: 1982-04-01 01:00:00+12:00: dst_offset: acetz 3600; zoneinfo 10800
402235140: 1982-09-30 23:59:00+12:00: dst_offset: acetz 3600; zoneinfo 10800
417963600: 1983-04-01 01:00:00+12:00: dst_offset: acetz 3600; zoneinfo 10800
433771140: 1983-09-30 23:59:00+12:00: dst_offset: acetz 3600; zoneinfo 10800
449586000: 1984-04-01 01:00:00+12:00: dst_offset: acetz 3600; zoneinfo 10800
465317940: 1984-09-30 02:59:00+12:00: dst_offset: acetz 3600; zoneinfo 10800
Zone Atlantic/Azores
-873676800: 1942-04-26 00:00:00+00:00: dst_offset: acetz 7200; zoneinfo 3600
-864000060: 1942-08-15 23:59:00+00:00: dst_offset: acetz 7200; zoneinfo 3600
-842832000: 1943-04-18 00:00:00+00:00: dst_offset: acetz 7200; zoneinfo 3600
-831340860: 1943-08-28 23:59:00+00:00: dst_offset: acetz 7200; zoneinfo 3600
-810777600: 1944-04-23 00:00:00+00:00: dst_offset: acetz 7200; zoneinfo 3600
-799891260: 1944-08-26 23:59:00+00:00: dst_offset: acetz 7200; zoneinfo 3600
-779328000: 1945-04-22 00:00:00+00:00: dst_offset: acetz 7200; zoneinfo 3600
-768441660: 1945-08-25 23:59:00+00:00: dst_offset: acetz 7200; zoneinfo 3600
Zone Atlantic/Madeira
-873680400: 1942-04-26 00:00:00+01:00: dst_offset: acetz 7200; zoneinfo 3600
-864003660: 1942-08-15 23:59:00+01:00: dst_offset: acetz 7200; zoneinfo 3600
-842835600: 1943-04-18 00:00:00+01:00: dst_offset: acetz 7200; zoneinfo 3600
-831344460: 1943-08-28 23:59:00+01:00: dst_offset: acetz 7200; zoneinfo 3600
-810781200: 1944-04-23 00:00:00+01:00: dst_offset: acetz 7200; zoneinfo 3600
-799894860: 1944-08-26 23:59:00+01:00: dst_offset: acetz 7200; zoneinfo 3600
-779331600: 1945-04-22 00:00:00+01:00: dst_offset: acetz 7200; zoneinfo 3600
-768445260: 1945-08-25 23:59:00+01:00: dst_offset: acetz 7200; zoneinfo 3600
Zone Europe/Berlin
-776563200: 1945-05-24 03:00:00+03:00: dst_offset: acetz 7200; zoneinfo 3600
-765936060: 1945-09-24 02:59:00+03:00: dst_offset: acetz 7200; zoneinfo 3600
-714610800: 1947-05-11 04:00:00+03:00: dst_offset: acetz 7200; zoneinfo 3600
-710380860: 1947-06-29 02:59:00+03:00: dst_offset: acetz 7200; zoneinfo 3600
Zone Europe/Gibraltar
-904518000: 1941-05-04 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-896050860: 1941-08-10 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-875487600: 1942-04-05 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-864601260: 1942-08-09 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-844038000: 1943-04-04 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-832546860: 1943-08-15 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-812588400: 1944-04-02 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-798073260: 1944-09-17 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-781052400: 1945-04-02 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-772066860: 1945-07-15 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-717030000: 1947-04-13 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-706748460: 1947-08-10 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
Zone Europe/Kyiv
-892522800: 1941-09-19 23:00:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
-857257260: 1942-11-02 02:59:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
Zone Europe/Lisbon
-873684000: 1942-04-26 00:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-864007260: 1942-08-15 23:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-842839200: 1943-04-18 00:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-831348060: 1943-08-28 23:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-810784800: 1944-04-23 00:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-799898460: 1944-08-26 23:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-779335200: 1945-04-22 00:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-768448860: 1945-08-25 23:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
Zone Europe/London
-904518000: 1941-05-04 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-896050860: 1941-08-10 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-875487600: 1942-04-05 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-864601260: 1942-08-09 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-844038000: 1943-04-04 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-832546860: 1943-08-15 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-812588400: 1944-04-02 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-798073260: 1944-09-17 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-781052400: 1945-04-02 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-772066860: 1945-07-15 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-717030000: 1947-04-13 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-706748460: 1947-08-10 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
Zone Europe/Madrid
-999482400: 1938-05-01 00:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-986090460: 1938-10-02 23:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
Zone Europe/Minsk
-899780400: 1941-06-27 23:00:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
-857257260: 1942-11-02 02:59:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
Zone Europe/Moscow
-1539493200: 1921-03-21 00:00:00+05:00: dst_offset: acetz 7200; zoneinfo 3600
-1525323660: 1921-08-31 23:59:00+05:00: dst_offset: acetz 7200; zoneinfo 3600
Zone Europe/Paris
-796266060: 1944-10-08 00:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-781052400: 1945-04-02 03:00:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
-766623660: 1945-09-16 02:59:00+02:00: dst_offset: acetz 7200; zoneinfo 3600
Zone Europe/Riga
-899521200: 1941-06-30 23:00:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
-857257260: 1942-11-02 02:59:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
Zone Europe/Simferopol
-888894000: 1941-10-31 23:00:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
-857257260: 1942-11-02 02:59:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
Zone Europe/Tallinn
-892954800: 1941-09-14 23:00:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
-857257260: 1942-11-02 02:59:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
Zone Europe/Vilnius
-900126000: 1941-06-23 23:00:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
-857257260: 1942-11-02 02:59:00+02:00: dst_offset: acetz 3600; zoneinfo -3600
Zone Pacific/Rarotonga
279714600: 1978-11-12 01:00:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
289387740: 1979-03-03 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
309952800: 1979-10-28 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
320837340: 1980-03-01 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
341402400: 1980-10-26 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
352286940: 1981-02-28 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
372852000: 1981-10-25 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
384341340: 1982-03-06 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
404906400: 1982-10-31 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
415790940: 1983-03-05 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
436356000: 1983-10-30 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
447240540: 1984-03-03 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
467805600: 1984-10-28 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
478690140: 1985-03-02 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
499255200: 1985-10-27 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
510139740: 1986-03-01 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
530704800: 1986-10-26 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
541589340: 1987-02-28 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
562154400: 1987-10-25 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
573643740: 1988-03-05 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
594208800: 1988-10-30 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
605093340: 1989-03-04 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
625658400: 1989-10-29 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
636542940: 1990-03-03 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
657108000: 1990-10-28 00:30:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
667992540: 1991-03-02 23:59:00-09:30: dst_offset: acetz 1800; zoneinfo 3600
```

<a name="Benchmarks"></a>
## Benchmarks

The [utils/benchmark](utils/benchmark) script is an informal
benchmarking of 4 Python timezone libraries: `acetimepy`, `pytz`, `dateutil` and
`zoneinfo`. The results are:

```
+-------------------+----------------+----------------+
| Time Zone Library | comp to epoch  | epoch to comp  |
|                   | (micros/iter)  | (micros/iter)  |
|-------------------+----------------+----------------|
| acetimepy         |         10.963 |         13.475 |
| dateutil          |          5.960 |          7.257 |
| pytz              |         16.244 |         15.514 |
| zoneinfo          |          1.409 |          0.709 |
+-------------------+----------------+----------------+
```

**Legend**:

* "comp to epoch"
    * date-time component to epoch seconds conversion using the
      `datetime.timestamp()` function
* "epoch to comp"
    * epoch seconds to date-time component conversion using
      `datetime.fromtimestamp()` function

<a name="SystemRequirements"></a>
## System Requirements

For end-users of the library:

* Python 3.7 or newer

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
