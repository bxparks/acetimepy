# Changelog

* Unreleased
    * Add tests for creating `acetz` directly from a ZoneInfo entry, instead
      of going through the ZoneManager.
    * Add Instllation, Usage, and other documentation to README.md.
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
