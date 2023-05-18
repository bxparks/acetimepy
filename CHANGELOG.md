# Changelog

* Unreleased
* 0.7.0 (2023-05-18, TZDB 2023c)
    * Rename project and packages
        * Rename project from `AceTimePython` to `acetimepy` to be more
          compatible with Python conventions.
        * Rename `zonedb_types.py` to `typing.py`.
        * Rename `acetime.acetz` (acetz.py) to `acetime.timezone` (timezone.py).
    * Simplify handling of Links
        * Remove `follow_link` flag from `acetz.tzfullname().
        * Add `acetz.targetname()` which returns the target if Link.
        * Regenerate `zonedb` with `eras` field populated for Links.
    * Change `ZoneManager.gettz(zone_name)` to return `None` instead of raising
      an exception if the `zone_name` is not found. This is more consistent with
      the behavior of
      [dateutil.tz.gettz()](https://dateutil.readthedocs.io/en/stable/tz.html).
    * Move `utils/zinfo.py` from `AceTimeTools` project.
* 0.6.1 (2023-04-01, TZDB 2023c)
    * Upgrade TZDB from 2023b to 2023c.
        * https://mm.icann.org/pipermail/tz-announce/2023-March/000079.html
            * "This release's code and data are identical to 2023a.  In other
              words, this release reverts all changes made in 2023b other than
              commentary, as that appears to be the best of a bad set of
              short-notice choices for modeling this week's daylight saving
              chaos in Lebanon."
    * AceTimePython is forced to upgrade to 2023c, because we skipped 2023a and
      went directly to 2023b, which is being rolled back by 2023c.
* 0.6.0 (2023-03-24, TZDB 2023b)
    * Upgrade TZDB from 2022g to 2023b
        * 2023a skipped because it came out only a day earlier.
        * 2023a: https://mm.icann.org/pipermail/tz-announce/2023-March/000077.html
            * Egypt now uses DST again, from April through October.
            * This year Morocco springs forward April 23, not April 30.
            * Palestine delays the start of DST this year.
            * Much of Greenland still uses DST from 2024 on.
            * America/Yellowknife now links to America/Edmonton.
            * tzselect can now use current time to help infer timezone.
            * The code now defaults to C99 or later.
            * Fix use of C23 attributes.
        * 2023b: https://mm.icann.org/pipermail/tz-announce/2023-March/000078.html
            * Lebanon delays the start of DST this year.
    * `zonedb_types.py`
        * Rename `rules_delta_offset` to `era_delta_offset` for better
         self-documentation.
        * Simplify `ZoneEra.zone_policy` so that it is None when the
          corresponding 'RULES` field in the TZ files is 'hh:mm' or '-'.
    * `acetime/zonedb/`
        * Extend start and until years to `[1800,10000)`.
        * Change MIN and MAX years to +/-32767.
        * Add 'Original Years' and 'Generated Years' in file headers.
    * Break cyclic dependency when generating `zonedb`
        * Use `--skip_bufestimator` which allows AceTimeTools to generate
          zonedb without depending on AceTimePython itself.
    * `zone_processor.py`
        * Remove obsolete `use_python_transition` option.
        * Always use PEP495 compatible algorithm.
* 0.5.6 (2022-12-04, TZDB 2022g)
    * Upgrade TZDB from 2022f to 2022g
        * https://mm.icann.org/pipermail/tz-announce/2022-November/000076.html
            * The northern edge of Chihuahua changes to US timekeeping.
            * Much of Greenland stops changing clocks after March 2023.
            * Fix some pre-1996 timestamps in northern Canada.
            * C89 is now deprecated; please use C99 or later.
            * Portability fixes for AIX, libintl, MS-Windows, musl, z/OS
            * In C code, use more C23 features if available.
            * C23 timegm now supported by default
            * Fixes for unlikely integer overflows
    * Incorporate notable `zone_policies.py` comments into notable
      `zone_infos.py`.
* 0.5.5 (2022-11-02, TZDB 2022f)
    * Upgrade TZDB from 2022e to 2022f
        * https://mm.icann.org/pipermail/tz-announce/2022-October/000075.html
			* Mexico will no longer observe DST except near the US border.
			* Chihuahua moves to year-round -06 on 2022-10-30.
			* Fiji no longer observes DST.
			* Move links to 'backward'.
			* In vanguard form, GMT is now a Zone and Etc/GMT a link.
			* zic now supports links to links, and vanguard form uses this.
			* Simplify four Ontario zones.
			* Fix a Y2438 bug when reading TZif data.
			* Enable 64-bit time_t on 32-bit glibc platforms.
			* Omit large-file support when no longer needed.
			* In C code, use some C23 features if available.
			* Remove no-longer-needed workaround for Qt bug 53071.
* 0.5.4 (2022-10-22, TZDB 2022e)
    * Extend zonedb range from `[1974,2050)` to `[1974,10000)` by using
      `is_terminal_year()` to speed up the `bufestimate.py` algorithm.
    * Upgrade TZDB from 2022d to 2022e
        * https://mm.icann.org/pipermail/tz-announce/2022-October/000074.html
            * Jordan and Syria switch from +02/+03 with DST to year-round +03.
* 0.5.3 (2022-10-06, TZDB 2022d)
    * Upgrade TZDB from 2022b to 2022d
        * 2022c
            * https://mm.icann.org/pipermail/tz-announce/2022-August/000072.html
                * Work around awk bug in FreeBSD, macOS, etc.
                * Improve tzselect on intercontinental Zones.
            * Skipped because there were no changes that affected AceTime.
        * 2022d
            * https://mm.icann.org/pipermail/tz-announce/2022-September/000073.html
                * Palestine transitions are now Saturdays at 02:00.
                * Simplify three Ukraine zones into one.
* 0.5.2 (2022-08-13, TZDB 2022b)
    * Upgrade to TZDB 2022b.
        * https://mm.icann.org/pipermail/tz-announce/2022-August/000071.html
            * Chile's DST is delayed by a week in September 2022.
            * Iran no longer observes DST after 2022.
            * Rename Europe/Kiev to Europe/Kyiv.
            * Finish moving duplicate-since-1970 zones to 'backzone'.
* 0.5.1 (2022-03-20, TZDB 2022a)
    * Update to TZDB 2022a.
        * https://mm.icann.org/pipermail/tz-announce/2022-March.txt
        * "Palestine will spring forward on 2022-03-27, not -03-26."
    * No changes to code.
* 0.5.0 (2022-02-14, TZDB 2021e)
    * Regenerate `zonedb/` using latest AceTimeTool which identifies notable
      Zones and Policies whose DST shifts are not exactly 0:00 or 1:00. No
      actual data change. Notable policies relevant from 1974 until 2050 are:
        * ZonePolicy Cook: DST shift 0:30
        * ZonePolicy DR: DST shift 0:30
        * ZonePolicy Eire: DST shift -1:00
        * ZonePolicy LH: DST shift 0:30
        * ZonePolicy Morocco: DST shift -1:00
        * ZonePolicy Namibia: DST shift -1:00
        * ZonePolicy StJohns: DST shift 2:00
        * ZonePolicy Troll: DST shift 2:00
        * ZonePolicy Uruguay: DST shift 0:30 or 1:30
    * Change Link entries from "hard links" to "symbolic links".
        * TimeZone objects now know whether it is a Link or a Zone.
        * Regenerate Link entries in `zonedb/`.
        * Tracks a similar change to `zonedb/` and `zonedbx/` database
          of the AceTime library.
    * Add `acetz.islink()` method which returns `True` if timezone is a Link
      entry instead of a Zone entry.
    * Add `acetz.tzfullname()` method.
        * Returns the full name of the time zone (e.g. `America/Los_Angeles`).
        * Returns the full name of the target time zone of a Link if the
          `follow_link` parameter is given.
        * See (TimeZone Full Name)[README.md#TimeZoneFullName] section.
* 0.4.0 (2021-12-29, TZDB 2021e)
    * Rename `src/acetime/zoneinfo` to `zonedb`.
    * Add typing info to `zonedb` generated files.
    * Add zone context info (`TZDB_VERSION`, `START_YEAR`, `UNTIL_YEAR`) to
      `zone_infos.py`.
    * Create `utils/Variance/report_zoneinfo.py`
        * To compare `acetime` and Python 3.9 `zoneinfo` packages.
        * Add variance report into README.md.
    * Move `benchmarks/AcetzBenchmark/` to `utils/AcetzBenchmark/`.
* 0.3.0 (2021-12-02, TZDB 2021e)
    * Consolidate `AcetzBenchmark`, add `generate_table.py` and `README.md`
      generator.
    * Add support for `zoneinfo` library from Python 3.9, and
      `backports.zoneinfo` for 3.8 and 3.7.
* 0.2.1 (2021-10-28, TZDB 2021e)
    * Add `AcetzBenchmark` to compare speed of `acetz` with `dateutil.tz`
      and `pytz`.
    * Update to TZDB 2021e.
        * https://mm.icann.org/pipermail/tz-announce/2021-October/000069.html
        * Palestine will fall back 10-29 (not 10-30) at 01:00.
* 0.2 (2021-10-18, TZDB 2021d)
    * Add tests for creating `acetz` directly from a ZoneInfo entry, instead
      of going through the ZoneManager.
    * Add Installation, Usage, and other documentation to README.md.
    * Upgrade to TZDB 2021d.
* 0.1 (2021-10-06, TZDB 2021c)
    * `zone_processor.py`
        * Correctly attached the UTC offsets of `start_date_time` of a
          `MatchingEra` to the previous `MatchingEra`.
        * Improve detection of an exact match between a `Transition` and the
          start time of its `MatchingEra`.
            * Previously, the `start_date_time` would be compared to only one
              of the 'w', 's' or 'u' versions of the `transition_time`,
              depending on the `modifier` of the `start_date_time`.
            * Now, the `start_date_time` is converted into all 3 units (using
              the last transition of the previous `MatchingEra`). If any of
              them match the corresponding `transition_time_{w,s,u}` times,
              the Transition is considered to an exact match to the start of the
              `MatchingEra`.
            * Resolves all validation errors between Python `acetime.acetz`
              class and the Hinnant `date` library.
    * Replace `acetz.getz()` with `ZoneManager.gettz()` whose `ZoneManager`
      class takes a zone registry.
        * Two pre-defined registries are: `zone_regsitry.ZONE_REGISTRY` and
          `zone_regsitry.ZONE_AND_LINK_REGISTRY`.
    * Upgrade to TZDB 2021c.
* (2021-09-08, TZDB 2021a)
    * Initial split from
      [AceTimeTools](https://github.com/bxparks/AceTimeTools).
