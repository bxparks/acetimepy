# AceTime for Python

An implementation of the Python
[tzinfo](https://docs.python.org/3/library/datetime.html#tzinfo-objects) class
in the Python standard `datetime` package. Provides an `acetz` class that
implements the same algorithm as the
[AceTime](https://github.com/bxparks/AceTime) for Arduino. Supports all time
zones from the [IANA TZ database](https://www.iana.org/time-zones). Custom
subsets of the full TZ database can be created and used to save memory.

This library provides a subset of the capabilities of:

* pytz (https://pypi.org/project/pytz/)
* dateutil (https://pypi.org/project/python-dateutil/)

**Version**: (2021-09-08, Initial split from AceTimeTools)

**Changelog**: [CHANGELOG.md](CHANGELOG.md)

<a name="License"></a>
## License

[MIT License](https://opensource.org/licenses/MIT)

<a name="FeedbackAndSupport"></a>
## Feedback and Support

If you have any questions, comments and other support questions about how to
use this library, please use the
[GitHub Discussions](https://github.com/bxparks/AceTimePython/discussions)
for this project. If you have bug reports or feature requests, please file a
ticket in [GitHub Issues](https://github.com/bxparks/AceTimePython/issues).
I'd love to hear about how this software and its documentation can be improved.
I can't promise that I will incorporate everything, but I will give your ideas
serious consideration.

Please refrain from emailing me directly unless the content is sensitive. The
problem with email is that I cannot reference the email conversation when other
people ask similar questions later.

<a name="Authors"></a>
## Authors

* Created by Brian T. Park (brian@xparks.net).
