# Changelog

* Unreleased
* v0.5.3 (2022-10-06, TZDB 2022d)
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
* v0.5.2 (2022-08-13, TZDB 2022b)
    * Upgrade to TZDB 2022b.
        * https://mm.icann.org/pipermail/tz-announce/2022-August/000071.html
            * Chile's DST is delayed by a week in September 2022.
            * Iran no longer observes DST after 2022.
            * Rename Europe/Kiev to Europe/Kyiv.
            * Finish moving duplicate-since-1970 zones to 'backzone'.
* v0.5.1 (2022-03-20, TZDB 2022a)
    * Update to TZDB 2022a.
        * https://mm.icann.org/pipermail/tz-announce/2022-March.txt
        * "Palestine will spring forward on 2022-03-27, not -03-26."
    * No changes to code.
* v0.5.0 (2022-02-14, TZDB 2021e)
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
* v0.4.0 (2021-12-29, TZDB 2021e)
    * Rename `src/acetime/zoneinfo` to `zonedb`.
    * Add typing info to `zonedb` generated files.
    * Add zone context info (`TZDB_VERSION`, `START_YEAR`, `UNTIL_YEAR`) to
      `zone_infos.py`.
    * Create `utils/Variance/report_zoneinfo.py`
        * To compare `acetime` and Python 3.9 `zoneinfo` packages.
        * Add variance report into README.md.
    * Move `benchmarks/AcetzBenchmark/` to `utils/AcetzBenchmark/`.
* v0.3.0 (2021-12-02, TZDB 2021e)
    * Consolidate `AcetzBenchmark`, add `generate_table.py` and `README.md`
      generator.
    * Add support for `zoneinfo` library from Python 3.9, and
      `backports.zoneinfo` for 3.8 and 3.7.
* v0.2.1 (2021-10-28, TZDB 2021e)
    * Add `AcetzBenchmark` to compare speed of `acetz` with `dateutil.tz`
      and `pytz`.
    * Update to TZDB 2021e.
        * https://mm.icann.org/pipermail/tz-announce/2021-October/000069.html
        * Palestine will fall back 10-29 (not 10-30) at 01:00.
* v0.2 (2021-10-18, TZDB 2021d)
    * Add tests for creating `acetz` directly from a ZoneInfo entry, instead
      of going through the ZoneManager.
    * Add Installation, Usage, and other documentation to README.md.
    * Upgrade to TZDB 2021d.
* v0.1 (2021-10-06, TZDB 2021c)
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
