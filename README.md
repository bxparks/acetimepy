# AceTime for Python

This library provides the `acetz` class which is an implementation of the
[tzinfo](https://docs.python.org/3/library/datetime.html#tzinfo-objects)
abstract class in the Python standard `datetime` package. The timezone algorithm
used by `acetz` is implemented by the `zone_processor` class and is identical to
the one used by the `ExtendedZoneProcessor` class in the
[AceTime](https://github.com/bxparks/AceTime) library for Arduino.

The underlying zoneinfo database is derived from the [IANA TZ
database](https://www.iana.org/time-zones) by the same
[AceTimeTools](https://github.com/bxparks/AceTimeTools) project  used to
generate the TZ database for AceTime. By default, it contains all Zone and Link
entries from the year 2000 until 2050. Custom subsets of the full TZ database
can be created to save memory.

The `acetz` class should be a drop-in replacement for the equivalent `tzinfo`
class from the following Python libraries:

* pytz (https://pypi.org/project/pytz/)
* dateutil (https://pypi.org/project/python-dateutil/)
* zoneinfo (https://docs.python.org/3/library/zoneinfo.html)

The initial motivation of this library was to provide an easier prototyping
environment for the algorithms used by the `ExtendedZoneProcessor` class in the
`AceTime` library. That motivation became mostly moot after
[EpoxyDuino](https://github.com/bxparks/EpoxyDuino) became a suitable
environment for developing AceTime on a Linux desktop.

Currently, the two main purposes of this library are:

1) Validating the AceTime `ExtendedZoneProcessor` class through the
   [AceTimeValidation](https://github.com/bxparks/AceTimeValidation) project.
2) Exploring the feasibility of porting this library to
   [MicroPython](https://micropython.org/) to bring
   support for IANA timezones to that environment.

**Version**: v0.3.0 (2021-12-02, TZDB 2021e)

**Changelog**: [CHANGELOG.md](CHANGELOG.md)

**See Also**:
* AceTime: https://github.com/bxparks/AceTime
* AceTimeTools: https://github.com/bxparks/AceTimeTools
* AceTimeValidation: https://github.com/bxparks/AceValidation

## Table Of Contents

* [Installation](#Installation)
* [Usage](#Usage)
    * [Package Structure](#PackageStructure)
    * [ZoneManager and acetz](#ZoneManagerAndAcetz)
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
$ git clone https://github.com/bxparks/AceTimePython
$ cd AceTimePython
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

<a name="PackageStructure"></a>
### Package Structure

The AceTimePython library provides the top-level package named `acetime`. There
are 2 main modules under `acetime`:

* `acetime.acetz`
* `acetime.zone_processor`

Normally, only the `acetz` module will be needed by the end-user. The
`zone_processor` package is mostly an internal implementation detail.

Within `acetz` module, there are 2 classes that the end-user will normally use:

* `acetime.acetz.ZoneManager`
* `acetime.acetz.acetz` (subclass of `datetime.tzinfo`)

The TZ database files are located in the `acetime.zonedbpy` subpackage. There
are 3 modules here:

* `acetime.zonedbpy.zone_infos`
* `acetime.zonedbpy.zone_policies`
* `acetime.zonedbpy.zone_registry`

<a name="ZoneManagerAndAcetz"></a>
### ZoneManager and acetz

Normally, the `acetz` class will be instantiated through the `ZoneManager`
class. An instance of a `ZoneManager` will need to be created and initialized
with a registry of the zones in the TZ database. The
`acetime.zonedbpy.zone_registry` module provides 2 pre-generated registries:

* `acetime.zonedbpy.zone_registry.ZONE_REGISTRY`
    * contains 377 Zone entries as of TZDB 2021c
* `acetime.zonedbpy.zone_registry.ZONE_AND_LINK_REGISTRY`
    * contains all 594 Zone and Link entries as of TZDB 2021c

We can then create an instance of `acetz` for a specific zone through the
ZoneManager:

```Python
from acetime.acetz import acetz, ZoneManager
from acetime.zonedbpy.zone_registry import ZONE_REGISTRY
from acetime.common import SECONDS_SINCE_UNIX_EPOCH

zone_manager = ZoneManager(ZONE_REGISTRY)

def do_something():
    tz = zone_manager.gettz('America/Los_Angeles')

    # Create date from epoch seconds
    epoch_seconds = 7984800
    unix_seconds = epoch_seconds + SECONDS_SINCE_UNIX_EPOCH
    dte = datetime.fromtimestamp(unix_seconds, tz=tz)

    # Create date from components
    dtc = datetime(2000, 4, 2, 3, 0, 0, tzinfo=tz)

    assert dte == dtc
```

<a name="DateTimeFold"></a>
### DateTime Fold

The `acetz` class supports the `fold` parameter in
[`datetime`](https://docs.python.org/3/library/datetime.html#datetime-objects)
which was introduced in Python 3.6.

<a name="SystemRequirements"></a>
## System Requirements

For end-users of the library:

* Python 3.7 or newer

To generate the `zonedbpy` TZ database:

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
Discussions](https://github.com/bxparks/AceTimePython/discussions) for this
project. If you have bug reports, please file a ticket in [GitHub
Issues](https://github.com/bxparks/AceTimePython/issues). Feature requests
should go into Discussions first because they often have alternative solutions
which are useful to remain visible, instead of disappearing from the default
view of the Issue tracker after the ticket is closed.

Please refrain from emailing me directly unless the content is sensitive. The
problem with email is that I cannot reference the email conversation when other
people ask similar questions later.

<a name="Authors"></a>
## Authors

* Created by Brian T. Park (brian@xparks.net).
