# Copyright 2018 Brian T. Park
#
# MIT License

"""
A Python version of the latest AceTime/ExtendedZoneProcessor class to replicate
its internal resource consumption, so that we can get an accurate maximum buffer
size for its TransitionStorage.
"""

import sys
import logging
from datetime import datetime
from datetime import timedelta
from typing import List
from typing import NamedTuple
from typing import Optional
from typing import Tuple
from typing import cast

from .common import EPOCH_YEAR
from .common import INVALID_YEAR
from .common import MIN_YEAR
from .common import MAX_TO_YEAR
from .common import to_unix_seconds
from .common import calc_day_of_month
from .date_tuple import YearMonthTuple
from .date_tuple import DateTuple
from .date_tuple import datetime_to_datetuple
from .date_tuple import normalize_date_tuple
from .date_tuple import subtract_date_tuple
from .transition import Transition
from .transition import TransitionStorage
from .transition import MatchingEra
from .transition import print_transitions
from .transition import check_transitions_sorted
from .typing import ZoneRule
from .typing import ZoneEra
from .typing import ZoneInfo


ACETIME_EPOCH = datetime(EPOCH_YEAR, 1, 1)  # in UTC


class BufferSizeInfo(NamedTuple):
    """A tuple containings the number of active transitions and the current
    buffer_size of TransitionStorage.
    """
    active_size: int
    buffer_size: int


class OffsetInfo(NamedTuple):
    """Various bits of the Transition information at the current time.
    """
    total_offset: int  # total_offset = utc_offset + dst_offset
    utc_offset: int  # seconds
    dst_offset: int  # seconds
    abbrev: str  # short abbreviations
    fold: int  # same meaning as datetime.fold


def to_offset_info(transition: Transition, fold: int) -> OffsetInfo:
    """Convert a Transition and fold into a OffsetInfo.
    """
    return OffsetInfo(
        transition.offset_seconds + transition.delta_seconds,
        transition.offset_seconds,
        transition.delta_seconds,
        transition.abbrev,
        fold,
    )


class TransitionMatch(NamedTuple):
    """The result of a _find_transition_for_seconds().
    * fold=0 means there was no overlap with the previous transition
    * fold=1 means there was an overlap with the previous transition
    """
    transition: Transition
    fold: int


# Various comparison states when comparing the Transition transition_time
# to the enclosing MatchingEra start_date_time and until_date_time.
MATCH_STATUS_FAR_PAST = -2
MATCH_STATUS_PRIOR = -1
MATCH_STATUS_EXACT_MATCH = 0
MATCH_STATUS_WITHIN_MATCH = 1
MATCH_STATUS_FAR_FUTURE = 2


def _match_status_is_active(match_status: int) -> bool:
    return (
        match_status == MATCH_STATUS_EXACT_MATCH
        or match_status == MATCH_STATUS_WITHIN_MATCH
        or match_status == MATCH_STATUS_PRIOR
    )


class ZoneProcessor:
    """Extract DST transition information for a given ZoneInfo. The
    DST transition information can be retrieved using the following methods:

    * get_timezone_info_for_seconds(): get info using epoch_seconds (from
        2000-01-01 00:00:00 UTC)
    * get_timezone_info_for_datetime(): get info using a 'datetime.datetime'
        instance

    The DST transition information is returned as an OffsetInfo tuple
    contain (total_offset, utc_offset, dst_offset, abbrev, fold) which is valid
    at the given epoch_seconds or 'datetime'.

    Both get_timezone_info_for_seconds() and get_timezone_info_for_datetime()
    call init_for_year() using a window size of 14 months around the closest
    'year' to the given argument. The 'closest' year could be (year-1) if the
    datetime was on Jan 1 of the following year in UTC time.

    The init_for_year() method calculates the relevant Transitions for the given
    year and caches results. Subsequent queries for different epoch_seconds or
    'datetime' will be efficient if the closest 'year' is the same. See
    init_for_year() for high level explanation of the internal algorithm.

    Usage:
        zone_processor = ZoneProcessor(zone_info [, debug])

        # Validate matches and transitions
        zone_processor.init_for_year(args.year)
        zone_processor.print_matches_and_transitions()

        # Get OffsetInfo for an epoch_seconds.
        info = zone_processor.get_timezone_info_for_seconds(epoch_seconds)

        # Get OffsetInfo for a datetime.
        info = zone_processor.get_timezone_info_for_datetime(dt)
    """

    def __init__(
        self,
        zone_info: ZoneInfo,
        debug: bool = False,
    ):
        """Constructor.

        Args:
            zone_info (dict): one of the ZONE_INFO_xxx constants from
                zone_infos.py. It can contain a reference to a zone_policy_data
                map. We need to convert these into ZoneEra and ZoneRule classes.
            debug (bool): set to True to enable logging
        """
        self.zone_info = zone_info
        self.debug = debug

        # Used by init_*() to indicate the current year of interest.
        self.year = 0

        # List of ZoneEra which match the interval of interest.
        self.matches: List[MatchingEra] = []

        # List of active Transition objects for the year given to
        # init_for_year().
        self.transitions: List[Transition] = []

        # Indexes to keep track of the high water mark for the C++
        # implementation.
        self.transition_storage = TransitionStorage()

    def get_transition_for_seconds(
        self,
        epoch_seconds: int,
    ) -> Optional[Transition]:
        """Return Transition for the given epoch_seconds.

        TOOD: Does not seem to be used at all. Remove?
        """
        self._init_for_second(epoch_seconds)
        tmatch = self._find_transition_for_seconds(epoch_seconds)
        return tmatch.transition if tmatch else None

    def get_transition_for_datetime(
        self,
        dt: datetime,
    ) -> Optional[Transition]:
        """Return Transition for the given datetime.

        TODO: Used only in zinfo.py and test_zone_processor.py. I think this
        could be replaced by get_timezone_info_for_datetime().
        """
        self.init_for_year(dt.year)
        return self._find_transition_for_datetime(dt)

    def get_timezone_info_for_seconds(
        self,
        epoch_seconds: int
    ) -> Optional[OffsetInfo]:
        """Return the OffsetInfo of the given epoch_seconds.
        """
        self._init_for_second(epoch_seconds)

        tmatch = self._find_transition_for_seconds(epoch_seconds)
        return (
            to_offset_info(tmatch.transition, tmatch.fold)
            if tmatch
            else None
        )

    def get_timezone_info_for_datetime(
        self,
        dt: datetime,
    ) -> Optional[OffsetInfo]:
        """Return the OffsetInfo of the Transition for a given datetime.
        """
        self.init_for_year(dt.year)
        transition = self._find_transition_for_datetime(dt)
        if not transition:
            return None
        return to_offset_info(transition, fold=dt.fold)

    def init_for_year(self, year: int) -> None:
        """Initialize the Matches and Transitions for the year. Call this
        explicitly before accessing self.matches, self.transitions, and
        self.all_candidate_transitions. The high level algorithm is as follows:

        * Extract the list of ZoneEras which overlap with the given year
          and the given window size (e.g. 13, 14, 36 months). These
          are called MatchingEraes.
        * Find the list of Transitions corresponding to the MatchingEraes
          using _create_transitions_for_match().
        * Convert the transition times of the Transition objects into
          start and until times according to the UTC offset of each
          Transition.
        * Determine the start and until times of each transitions according
          to the wall time of each Transition.
        * Determine the time zone abbreviations (e.g. "PDT", "GMT") of
          each Transition.
        """
        if self.debug:
            logging.info(
                '==== %s: init_for_year(): year: %d',
                self.zone_info['name'], year)
        # Check if cache filled
        if self.year == year:
            if self.debug:
                logging.info(
                    '==== %s: init_for_year(): cached',
                    self.zone_info['name'])
            return

        self.year = year
        self.matches = []
        self.transitions = []
        self.transition_storage.clear()

        # Restrict transitions to the 14 months from Dec of the previous year
        # until Feb of the following year.
        start_ym = YearMonthTuple(year - 1, 12)
        until_ym = YearMonthTuple(year + 1, 2)

        if self.debug:
            logging.info('---- Step 1: Finding matches')
        self.matches = self._find_matches(start_ym, until_ym)

        if self.debug:
            logging.info('---- Step 2: Creating (raw) transitions')
        self._create_transitions(self.matches)
        if self.debug:
            print_transitions('All Transitions', self.transitions)

        # Some transitions from simple match may be in 's' or 'u', so
        # convert to 'w'.
        if self.debug:
            logging.info('---- Step 3: Fixing transitions times')
        _fix_transition_times(self.transitions)
        if self.debug:
            print_transitions('All Transitions', self.transitions)

        if self.debug:
            logging.info('---- Step 4: Generating start and until times')
        self._generate_start_until_times(self.transitions)
        if self.debug:
            print_transitions('All Transitions', self.transitions)

        if self.debug:
            logging.info('---- Step 5: Calculating abbreviations')
        self._calc_abbrev(self.transitions)
        if self.debug:
            print_transitions('All Transitions', self.transitions)

    def get_buffer_sizes(self) -> BufferSizeInfo:
        """Return the number of active transitions and the transition buffer
        size that was required to obtain them.
        """
        return BufferSizeInfo(
            active_size=len(self.transitions),
            buffer_size=self.transition_storage.index_beyond,
        )

    def is_terminal_year(self, year: int) -> bool:
        """Return true if the given `year` is large enough that it contains the
        transitions of the last rules of the zone, and any future year will
        cause no changes to the value of get_buffer_sizes().

        1) If year exceeds the last ZoneEra entry, then return True.
        2) If year is not in the last ZoneEra, return False.
        3) The year matches the last ZoneEra entry, so:
            3.1) If the last ZoneEra is a Simple ZoneEra (no reference to
                ZonePolicy), then return True.
            3.2) The last ZoneEra is Named ZoneEra (references a ZonePolicy):
                3.2.1) If there are upcoming Rules which haven't matched the
                       current year, return False.
                3.2.2) If all matching Rules are infinite or none, return True.
            3.3) Otherwise, some matching Rules are finite, so return False.
        """
        # The 'eras' is always defined, whether Zone or Link.
        zone_eras = self.zone_info.get('eras')
        assert zone_eras is not None

        # 1) Check if the year is beyond the last ZoneEra.
        zone_era = zone_eras[-1]
        until_year = zone_era['until_year']
        if year > until_year:  # check >= (until_year + 1), to be safe
            return True

        # 2) Check if year matches the last ZoneEra.
        prev_until_year = 0
        if len(zone_eras) > 1:
            prev_until_year = zone_eras[-2]['until_year']
        if year < prev_until_year:
            return False

        # 3.1) Check if the last ZoneEra is a Simple one.
        zone_policy = zone_era.get('zone_policy')
        if not zone_policy:
            return True

        # 3.2) Last ZoneEra was a Named era, so search the Rules of the Policy.
        rules = zone_policy['rules']
        num_finite_matches = 0
        num_infinite_matches = 0
        for rule in rules:
            from_year = rule['from_year']
            if year < from_year:
                return False  # 3.2.1
            else:  # year >= from_year
                to_year = rule['to_year']
                if to_year == MAX_TO_YEAR:
                    num_infinite_matches += 1
                elif year <= to_year:
                    num_finite_matches += 1
        if num_finite_matches == 0:
            return True  # 3.2.2

        # 3.3) Otherwise, some matching Rules are finite.
        return False

    def is_link(self) -> bool:
        return 'link_to' in self.zone_info

    def get_name(self) -> str:
        """Return the full name of the current ZoneInfo."""
        return self.zone_info['name']

    def get_target_name(self) -> str:
        """Return the full name of the target ZoneInfo if the current Zone
        is a Link. Otherwse, returns an empty string.
        """
        if self.is_link():
            zone_info = cast(ZoneInfo, self.zone_info.get('link_to'))
            return zone_info['name']
        else:
            return ""

    # ------------------------------------------------------------------------
    # The following methods are designed to be used internally.
    # ------------------------------------------------------------------------

    def _init_for_second(self, epoch_seconds: int) -> None:
        """Initialize the Transitions from the given epoch_seconds.
        """
        ldt = datetime.utcfromtimestamp(to_unix_seconds(epoch_seconds))
        self.init_for_year(ldt.year)

    def _find_transition_for_seconds(
        self,
        epoch_seconds: int,
    ) -> Optional[TransitionMatch]:
        """Return the matching transition along with the 'fold' information.
        Return None if not found.

        * fold==0 if the transition was the first matching transition
        * fold==1 if the transition was the second of an overlapping match.
        """
        # Use indexing instead of iterator because we need access to the
        # transition[match-2] element, and it's much easier to do that with
        # indexing. Scan until we get to a transition *just* after the one that
        # matches.
        matching_index = -1
        for i in range(len(self.transitions)):
            transition = self.transitions[i]
            if transition.start_epoch_second > epoch_seconds:
                break
            matching_index = i

        # If no match, return None.
        if matching_index == -1:
            return None

        fold = self._determine_fold(epoch_seconds, matching_index)

        transition_match = TransitionMatch(
            self.transitions[matching_index],
            fold,
        )
        return transition_match

    def _determine_fold(self, epoch_seconds: int, matching_index: int) -> int:
        """Determine the 'fold' by looking at the transition just before the
        matching one. If the prev and current transition overlap, *and* the
        epoch_seconds falls within the overlap, then set the fold to 1,
        otherwise 0.
        """
        if matching_index < 1:
            return 0

        overlap_interval = subtract_date_tuple(
            self.transitions[matching_index - 1].until_date_time,
            self.transitions[matching_index].start_date_time,
        )
        # No fold if the transition caused a gap.
        if overlap_interval <= 0:
            return 0

        transition_start = self.transitions[matching_index].start_epoch_second
        seconds_from_transition_start = epoch_seconds - transition_start
        # No fold if epoch_seconds is beyond the overlap interval.
        if seconds_from_transition_start >= overlap_interval:
            return 0

        return 1

    def _find_transition_for_datetime(
        self,
        dt: datetime,
    ) -> Optional[Transition]:
        """Return the match transition using an algorithm that works for
        Python's datetime.tzinfo and follows PEP 495
        (https://www.python.org/dev/peps/pep-0495/) to handle the 'fold'
        parameter in the 'datetime' within the fold and within the gap.

        * If the 'dt' is in the overlap:
            * return the earlier transition (earlier UTC) if dt.fold == 0,
            * return the later transition (later UTC) if dt.fold == 1.
        * If the 'dt' is in the gap:
            * return the earlier transition (later UTC) if dt.fold == 0,
            * return the later transition (earlier UTC) if dt.fold == 1,
            * see PEP 495 for details.
        """
        dt_time = datetime_to_datetuple(dt, 'w')

        prev_exact: Optional[Transition] = None
        prev_transition: Optional[Transition] = None
        for transition in self.transitions:
            start_time = transition.start_date_time
            until_time = transition.until_date_time

            exact_match = start_time <= dt_time and dt_time < until_time
            if exact_match:
                if dt.fold == 0:
                    return transition
                if prev_exact is not None:
                    # In the fold/overlap.
                    return transition
                prev_exact = transition
            elif start_time > dt_time:
                if prev_exact:
                    return prev_exact
                # In the gap.
                if dt.fold == 0:
                    return prev_transition
                else:
                    return transition

            prev_transition = transition

        return prev_exact or prev_transition

    def _find_matches(
        self,
        start_ym: YearMonthTuple,
        until_ym: YearMonthTuple,
    ) -> List[MatchingEra]:
        """Find the Zone Eras which overlap [start_ym, until_ym), ignoring
        day, time and timeSuffix. The start and until fields are truncated at
        the low and high end by start_ym and until_ym, respectively.

        When the epochSeconds is converted to a year using the UTC timezone, the
        actual local DateTime could be Dec 31 of the previous year, or Jan 1 of
        the following year. Unfortunately, we don't know the local time zone
        offset until we generate the Transitions of the local year, and we don't
        know the local year until we generate the Transitions. To get around
        this problem, we create a [start_ym, until_ym) interval that's slightly
        larger than the current year of interest.

        The size of the [start_ym, until_ym) is normally 14 months, from Dec of
        the previous year until Feb of the following year. This works well but
        often produces more candidate Transitions than absolutely necessary
        because the interval spans at least 3 whole years, and potentially 4
        years for the 'most recent prior year'.
        """
        # The 'eras' is defined for both Zones and Links.
        zone_eras = self.zone_info.get('eras')
        assert zone_eras is not None

        prev_match: Optional[MatchingEra] = None
        matches: List[MatchingEra] = []
        for zone_era in zone_eras:
            if _era_overlaps_interval(
                prev_match.zone_era if prev_match else None,
                zone_era,
                start_ym,
                until_ym,
            ):
                match = self._create_match(
                    prev_match, zone_era, start_ym, until_ym)
                if self.debug:
                    logging.info('_find_matches(): %s', match)
                matches.append(match)
                prev_match = match
        return matches

    def _create_transitions(self, matches: List[MatchingEra]) -> None:
        """Create the relevant transitions from the matching ZoneEras.
        """
        for match in matches:
            self._create_transitions_for_match(match)

    def _create_transitions_for_match(self, match: MatchingEra) -> None:
        """Determine if the given MatchingEra is a simple MatchingEra (contains
        an explicit DST offset) or named (references a named ZonePolicy to
        determine the DST offset). Then find the Transitions of the given match
        using the appropriate algorithm.
        """
        if self.debug:
            logging.info('_create_transitions_for_match(): %s', match)

        zone_era = match.zone_era
        zone_policy = zone_era.get('zone_policy')
        if not zone_policy:
            self._create_transitions_from_simple_match(match)
        else:
            self._create_transitions_from_named_match(match)

    def _create_transitions_from_simple_match(self, match: MatchingEra) -> None:
        """The zone_policy is None then the Zone Era itself defines the
        UTC offset and the abbreviation. Add the corresponding Transition into
        the Active pool of TransitionStorage immediately.
        """
        if self.debug:
            logging.info(
                '_create_transitions_from_simple_match(): %s', match)
        transition = Transition(
            matching_era=match,
            transition_time=match.start_date_time,
        )
        transition.match_status = MATCH_STATUS_EXACT_MATCH
        if self.debug:
            print_transitions('Simple Transition', [transition])
        match.last_transition = transition
        self.transitions.append(transition)
        self.transition_storage.push_transitions(1)

    def _create_transitions_from_named_match(self, match: MatchingEra) -> None:
        """Find the transitions of the named MatchingEra. The search for the
        relevant Transition occurs in 3 passes:

        1. Find the candidate Transitions defined by the MatchingEra using the
           *whole* years of the MatchingEra (i.e. ignoring the month, day, and
           time fields).
            * Whole years are used because the ZoneRules define recurring rules
              based on whole years.
            * This pass includes something called the "most recent prior"
              Transition, because we need to know the Transition that occurred
              just before the beginning of the given year.
        2. Fix the transition times.
            * Convert the transition_time to the wall time ('w') of the previous
              rule's time offset.
            * If the transition times are given in standard ('s') or UTC ('u')
              time, they are normalized to 'w'.
        3. Select the Transitions which are "active".
            * Active is determined by the entire date and time fields of
              MatchingEra (including month, day and time) fields.
        """
        if self.debug:
            logging.info('_create_transitions_from_named_match(): %s', match)

        # Pass 1: Find candidate transitions using whole years.
        if self.debug:
            logging.info(
                '---- Pass 1: Get candidate transitions for MatchingEra')
        zone_era = match.zone_era
        zone_policy = zone_era.get('zone_policy')
        assert zone_policy is not None
        policy_name = zone_policy['name']

        # assert isinstance(zone_policy, ZonePolicy)
        rules = zone_policy['rules']
        candidate_transitions = self._find_candidate_transitions(match, rules)
        if self.debug:
            print_transitions('Candidate Transitions', candidate_transitions)
        check_transitions_sorted(policy_name, candidate_transitions)
        self.transition_storage.pop_transitions(len(candidate_transitions))

        # Pass 2: Fix the transitions times, converting 's' and 'u' into 'w'
        # uniformly.
        if self.debug:
            logging.info('---- Pass 2: Fix transition times')
        _fix_transition_times(candidate_transitions)
        if self.debug:
            print_transitions('Candidate Transitions', candidate_transitions)
        check_transitions_sorted(policy_name, candidate_transitions)

        # Pass 3: Select only those Transitions which overlap with the actual
        # start and until times of the MatchingEra.
        if self.debug:
            logging.info('---- Pass 3: Select active transitions')
        try:
            transitions = self._select_active_transitions(candidate_transitions)
        except:  # noqa: E722
            logging.exception(
                "Zone '%s'; year '%04d'",
                self.zone_info['name'],
                self.year)
            raise
        if self.debug:
            print_transitions('Active Transitions', transitions)

        # Pass 4: Verify that the "most recent prior" Transition is properly
        # sorted.
        if self.debug:
            logging.info('---- Pass 4: Final check for sorted transitions')
        check_transitions_sorted(policy_name, transitions)
        if self.debug:
            print_transitions('Active Sorted Transition', transitions)

        # Save the last transition of the current MatchingEra.
        match.last_transition = transitions[-1]

        self.transitions.extend(transitions)
        self.transition_storage.push_transitions(len(transitions))

    def print_matches_and_transitions(self) -> None:
        logging.info('---- Buffer Size')
        logging.info('Max: %s', self.transition_storage.index_beyond)
        logging.info('---- Matches')
        for m in self.matches:
            logging.info(m)
        logging.info('---- Transitions')
        for t in self.transitions:
            logging.info(t)

    @staticmethod
    def _create_match(
        prev_match: Optional[MatchingEra],
        zone_era: ZoneEra,
        start_ym: YearMonthTuple,
        until_ym: YearMonthTuple,
    ) -> MatchingEra:
        """Create the Zone Match object for the given Zone Era, truncated at
        the low and high end by start_ym and until_ym:

        * MatchingEra.start_date_time is prev_era.until_time
        * MatchingEra.until_date_time is zone_era.until_time
        * MatchingEra.policy_name is '-', ':' or the string name of ZonePolicy

        The start_date_time of the current MatchingEra is determined by the
        UNTIL datetime of the prev_era, which uses the UTC offset of the
        *previous* era, not the current era. Therefore, the start_date_time and
        until_date_time is accurate to a resolution of one day. This is good
        enough to generate Transitions, which also will have dateTime fields
        accurate to within a day or so, assuming we don't have 2 DST transitions
        in a single day.

        See _fix_transition_times() which normalizes these start times to the
        wall time uniformly.

        A value of `prev_era==None` means the earliest possible ZoneEra.
        """
        if prev_match is None:
            start_date_time = DateTuple(
                y=MIN_YEAR, M=1, d=1, ss=0, f='w')
        else:
            prev_era = prev_match.zone_era
            start_date_time = DateTuple(
                y=prev_era['until_year'],
                M=prev_era['until_month'],
                d=prev_era['until_day'],
                ss=prev_era['until_seconds'],
                f=prev_era['until_time_suffix'])
        left_boundary = DateTuple(y=start_ym.y, M=start_ym.M, d=1, ss=0, f='w')
        if start_date_time < left_boundary:
            start_date_time = left_boundary

        until_date_time = DateTuple(
            y=zone_era['until_year'],
            M=zone_era['until_month'],
            d=zone_era['until_day'],
            ss=zone_era['until_seconds'],
            f=zone_era['until_time_suffix'])
        right_boundary = DateTuple(y=until_ym.y, M=until_ym.M, d=1, ss=0, f='w')
        if until_date_time > right_boundary:
            until_date_time = right_boundary

        return MatchingEra(
            start_date_time=start_date_time,
            until_date_time=until_date_time,
            zone_era=zone_era,
            prev_match=prev_match,
        )

    @staticmethod
    def _generate_start_until_times(transitions: List[Transition]) -> None:
        """Calculate the various start and until times of the Transitions in the
        following way:

        1) The 'until_date_time' of the previous Transition is the
           'transition_time' of the current Transition with no adjustments.
        2) The local 'start_date_time' of the current Transition is
           the current 'transition_time' - (prevOffset + prevDelta) +
           (currentOffset + currentDelta), which converts it into the UTC offset
           of the current transition.
        3) The 'start_epoch_second' of the current Transition is the
           'transition_time' using the UTC offset of the *previous*
           Transition.

        Got all that? Good, because I often cannot understand my own comments
        after a period of time.

        The 'transition_time' field is assumed to have been normalized into the
        'w' mode by calling _fix_transition_times() before this method is
        called.
        """

        # As before, bootstrap the prev transition with the first transition
        # so that we have a UTC offset to work with.
        prev = transitions[0]
        is_after_first = False
        for transition in transitions:
            # Transition time using the wall time of the previous Transition.
            tt = transition.transition_time_w

            # 1) Update the 'until_date_time' of the previous Transition.
            if is_after_first:
                prev.until_date_time = tt

            # 2) Calculate the current start_date_time by shifting the
            # transition time into the current UTC offset. This algorithm should
            # be able to handle transition time of 24:00 (or even 25:00) of the
            # previous day.
            secs = (tt.ss - prev.offset_seconds - prev.delta_seconds
                    + transition.offset_seconds + transition.delta_seconds)
            # If (secs < 0 or secs >= 24 * 60 * 60), then we shifted into a
            # different day. During debugging, it was useful to know that, but
            # not so useful in production code, so don't print anything.
            st = datetime(tt.y, tt.M, tt.d)
            st += timedelta(seconds=secs)
            transition.start_date_time = datetime_to_datetuple(st, tt.f)

            # 3) The epochSecond of the 'transition_time' is determined by the
            # UTC offset of the *previous* Transition. However, the
            # transition_time can be represented by an illegal time (e.g.
            # 24:00). So use the properly normalized start_date_time
            # (calculated above) with the *current* UTC offset.
            #
            # A previous version of this used a `timezone` object set to the
            # fixed `utc_offset_seconds`, then converted the timezone-naive `st`
            # object into a timezone-aware `st` object at that fixed `timezone`.
            # But this bring in the only dependency to the Python `timezone`
            # class which is unnecessary because we can calculate the epoch
            # seconds directly.
            utc_offset_seconds = (
                transition.offset_seconds + transition.delta_seconds)
            dt = st - timedelta(seconds=utc_offset_seconds)  # dt now in UTC
            epoch_second = int((dt - ACETIME_EPOCH).total_seconds())
            transition.start_epoch_second = epoch_second

            prev = transition
            is_after_first = True

        # Finally, fix the last transition's until time
        (udt, udts, udtu) = _expand_date_tuple(
            transition.until_date_time,
            transition.offset_seconds,
            transition.delta_seconds,
        )
        transition.until_date_time = udt

    @staticmethod
    def _calc_abbrev(transitions: List[Transition]) -> None:
        """Calculate the time zone abbreviations for each Transition.
        There are several cases:
        1) 'format' contains 'A/B', meaning 'A' for standard time, and 'B'
            for DST time.
        2) 'format' contains a %s, which substitutes the 'letter'
            2a) If 'letter' is '-', replace with nothing.
            2b) The 'format' could be just a '%s'.
        """
        for transition in transitions:
            format = transition.format
            delta_seconds = transition.delta_seconds

            index = format.find('/')
            if index >= 0:
                if delta_seconds == 0:
                    abbrev = format[:index]
                else:
                    abbrev = format[index + 1:]
            elif format.find('%s') >= 0:
                letter = transition.letter
                if letter == '-':
                    letter = ''
                abbrev = format % letter
            else:
                abbrev = format

            transition.abbrev = abbrev

    def _find_candidate_transitions(
        self,
        match: MatchingEra,
        rules: List[ZoneRule],
    ) -> List[Transition]:
        """Find candidate transition while filtering out ones which are
        obviously non-candidates. This reduces the size of the statically
        allocated Transitions array in the C++ implementation.
        """
        # If MatchEra.until_date_time is exactly Jan 1 00:00, set the end_year
        # to the prior year to avoid pulling Transitions in the next year which
        # do not need to be examined.
        start_y = match.start_date_time.y
        end_y = match.until_date_time.y
        until = match.until_date_time
        if until.M == 1 and until.d == 1 and until.ss == 0:
            end_y -= 1

        # Reserve prior Transition.
        prior_transition: Optional[Transition] = None
        self.transition_storage.push_transitions(1)

        transitions: List[Transition] = []
        for rule in rules:
            from_year = rule['from_year']
            to_year = rule['to_year']
            years = _get_interior_years(from_year, to_year, start_y, end_y)
            if self.debug:
                logging.info(
                    '_find_candidate_transitions(): '
                    '[%s,%s]: interior years: %s',
                    from_year, to_year, years)

            # Examine transitions in the interior years. Keep track of potential
            # prior transition.
            for year in years:
                transition = _create_transition_for_year(year, rule, match)
                self.transition_storage.push_transitions(1)  # free agent
                # Use fuzzy check to filter out transitions which cannot be
                # candidates.
                comp = _compare_transition_to_match_fuzzy(transition, match)
                if comp == MATCH_STATUS_PRIOR:
                    prior_transition = self._select_prior_transition(
                        prior_transition, transition)
                    # Free agent replaces prior transition.
                    self.transition_storage.pop_transitions(1)
                elif comp == MATCH_STATUS_WITHIN_MATCH:
                    # Free agent becomes a candidate transition, so no need
                    # to update the TransitionStorage buffer size.
                    _add_transition_sorted(transitions, transition)
                elif comp == MATCH_STATUS_FAR_FUTURE:
                    # Remove free agent because it's not used. In the C++ code,
                    # this is done implicitly, but in Python code, this must be
                    # done explicitly.
                    self.transition_storage.pop_transitions(1)
                else:
                    raise Exception(f"Invalid MATCH_STATUS {comp}")

            # Explicitly examine the transition of the prior year and compare
            # it with the other candidate prior transitions from above.
            prior_year = _get_most_recent_prior_year(
                from_year, to_year, start_y, end_y)
            if self.debug:
                logging.info('_find_candidate_transitions(): prior year: %s',
                             prior_year)
            if prior_year != INVALID_YEAR:
                transition = _create_transition_for_year(
                    prior_year, rule, match)
                self.transition_storage.push_transitions(1)
                prior_transition = self._select_prior_transition(
                    prior_transition, transition)
                self.transition_storage.pop_transitions(1)

        # Add the most recent prior transition if it exists. Otherwise, we need
        # to remove the reserved prior transition to match the buffer size of
        # the C++ code. The C++ code does this implicitly.
        if prior_transition:
            _add_transition_sorted(transitions, prior_transition)
        else:
            self.transition_storage.pop_transitions(1)

        return transitions

    @staticmethod
    def _select_prior_transition(
        prior_transition: Optional[Transition],
        transition: Transition,
    ) -> Transition:
        """Select the latest prior transition given the previous prior
        transition and the current transition.
        """
        if prior_transition:
            if transition.transition_time > prior_transition.transition_time:
                return transition
            else:
                return prior_transition
        else:
            return transition

    def _select_active_transitions(
        self,
        transitions: List[Transition],
    ) -> List[Transition]:
        """Determine the active Transisitions using the match_status field.
        The final result is returned in a new 'active_transitions' list, but in
        the C++ version, we can avoid allocating an extra array by filter on the
        'match_status' flag and resizing the transitions array.
        """
        if self.debug:
            logging.info('_select_active_transitions()')

        prior: Optional[Transition] = None
        for transition in transitions:
            prior = _process_transition_match_status(transition, prior)

        if prior:
            # Replace the transition_time with the MatchingEra's start_date_time
            # because start_date_time uses the UTC offset of the previous
            # MatchingEra, which is how we want to interpret the transition time
            # of the prior transition.
            prior.original_transition_time = prior.transition_time
            prior.transition_time = prior.matching_era.start_date_time

        active_transitions = []
        for transition in transitions:
            if _match_status_is_active(transition.match_status):
                active_transitions.append(transition)
        return active_transitions


def _process_transition_match_status(
    transition: Transition,
    prior: Optional[Transition],
) -> Optional[Transition]:
    """Determine if a transition is active with respect to the given match.
    This assumes that all Transitions have been fixed using
    _fix_transition_times().
    """
    match_status = _compare_transition_to_match(
        transition, transition.matching_era)
    transition.match_status = match_status

    if match_status == MATCH_STATUS_EXACT_MATCH:
        # This transition falls exactly on the match.start boundary. We
        # invalidate any previous prior transition candidate. And we set the
        # current prior to this exactly matching Transition to prevent any
        # other Transition from becoming the prior.
        if prior:
            prior.match_status = MATCH_STATUS_FAR_PAST
        prior = transition
    elif match_status == MATCH_STATUS_PRIOR:
        if prior:
            if transition.transition_time_u >= prior.transition_time_u:
                prior.match_status = MATCH_STATUS_FAR_PAST
                prior = transition
            else:
                transition.match_status = MATCH_STATUS_FAR_PAST
        else:
            prior = transition
    return prior


def _era_overlaps_interval(
    prev_era: Optional[ZoneEra],
    era: ZoneEra,
    start_ym: YearMonthTuple,
    until_ym: YearMonthTuple,
) -> bool:
    """Determines if era overlaps the interval [start_ym, until_ym),
    ignoring the day, time and timeSuffix. The start date of the current
    era is represented by the prev_era.UNTIL, so the interval of the current
    era is [start_era, until_era) = [prev_era.UNTIL, era.UNTIL). Overlap
    happens if (start_era < until_ym) and (until_era > start_ym). A
    'prev_era==None' means the earliest possible ZoneEra.
    """
    return (
        (
            prev_era is None
            or _compare_era_to_year_month(prev_era, until_ym.y, until_ym.M) < 0
        )
        and _compare_era_to_year_month(era, start_ym.y, start_ym.M) > 0
    )


def _compare_era_to_year_month(
    era: ZoneEra,
    year: int,
    month: int,
) -> int:
    """Compare the zone_era with year, returning -1, 0 or 1. The day of
    month is implicitly 1. Ignore the until_time_suffix suffix. Maybe it's
    not needed in this context?
    """
    if era['until_year'] < year: return -1  # noqa: E701
    if era['until_year'] > year: return 1  # noqa: E701
    if era['until_month'] < month: return -1  # noqa: E701
    if era['until_month'] > month: return 1  # noqa: E701
    if era['until_day'] > 1: return 1  # noqa: E701
    if era['until_seconds'] < 0: return -1  # noqa: E701
    if era['until_seconds'] > 0: return 1  # noqa: E701
    return 0


def _add_transition_sorted(
        transitions: List[Transition],
        transition: Transition,
) -> None:
    """Add the transition to the transitions array, using an Insertion Sort
    algorithm, so that 'transitions' array is always sorted by transition_time.

    In normal Python code, we would accumulate the unsorted 'transitions' list,
    then call 'sort()` after all the elements have been added. But this code is
    emulating the equivalent Arduino C++ code without without dynamic arrays and
    a sort() function. By using an incremental Insertion Sort algorithm, we can
    convert this into C++ more easily. The O(N^2) Insertion Sort algorithm
    should be more than fast enough since N <= ~7 (up to 4 interior transitions,
    plus 1 in Jan of the current year, plus 1 in Jan of the following year, and
    1 most recent prior transition.)
    """
    transitions.append(transition)
    for i in range(len(transitions) - 1, 0, -1):
        curr = transitions[i]
        prev = transitions[i - 1]
        if _compare_date_tuple(curr.transition_time, prev.transition_time) < 0:
            transitions[i - 1] = curr
            transitions[i] = prev


def _compare_date_tuple(a: DateTuple, b: DateTuple) -> int:
    if a.y < b.y: return -1  # noqa: E701
    if a.y > b.y: return 1  # noqa: E701
    if a.M < b.M: return -1  # noqa: E701
    if a.M > b.M: return 1  # noqa: E701
    if a.d < b.d: return -1  # noqa: E701
    if a.d > b.d: return 1  # noqa: E701
    return 0


def _expand_date_tuple(
    dt: DateTuple,
    offset_seconds: int,
    delta_seconds: int,
) -> Tuple[DateTuple, DateTuple, DateTuple]:
    """Convert 's', 'u', or 'w' time into the other 2 versions using the
    given base UTC offset and the delta DST offset. Return a tuple of
    *normalized* (wall, standard, utc) date tuples. The dates are normalized
    so that transitions occurring at 24:00:00 is moved to the next day.
    """
    delta_seconds = delta_seconds if delta_seconds else 0
    offset_seconds = offset_seconds if offset_seconds else 0

    if dt.f == 'w':
        dtw = dt
        dts = DateTuple(
            y=dt.y, M=dt.M, d=dt.d, ss=dtw.ss - delta_seconds, f='s')
        ss = dtw.ss - delta_seconds - offset_seconds
        dtu = DateTuple(y=dt.y, M=dt.M, d=dt.d, ss=ss, f='u')
    elif dt.f == 's':
        dts = dt
        dtw = DateTuple(
            y=dt.y, M=dt.M, d=dt.d, ss=dts.ss + delta_seconds, f='w')
        dtu = DateTuple(
            y=dt.y, M=dt.M, d=dt.d, ss=dts.ss - offset_seconds, f='u')
    elif dt.f == 'u':
        dtu = dt
        ss = dtu.ss + delta_seconds + offset_seconds
        dtw = DateTuple(y=dtu.y, M=dtu.M, d=dtu.d, ss=ss, f='w')
        dts = DateTuple(
            y=dtu.y, M=dtu.M, d=dtu.d, ss=dtu.ss + offset_seconds, f='s')
    else:
        logging.error("Unrecognized Rule.AT suffix '%s'; date=%s", dt.f, dt)
        sys.exit(1)

    dtw = normalize_date_tuple(dtw)
    dts = normalize_date_tuple(dts)
    dtu = normalize_date_tuple(dtu)

    return (dtw, dts, dtu)


def _fix_transition_times(transitions: List[Transition]) -> None:
    """Convert the transtion['transition_time'] to the wall time ('w') of
    the previous rule's time offset. The Transition time comes from either:

    1) The UNTIL field of the previous Zone Era entry, or
    2) The (in_month, on_day, at_seconds) fields of the Zone Rule.

    In most cases these times are specified as the wall clock 'w' by
    default, but a few cases use 's' (standard) or 'u' (utc). We don't need
    to support 'g' and 'z' because they mean exactly the same as 'u' and
    they don't appear anywhere in the current TZ files. The transformer.py
    will detect and filter those out.

    To convert these into the more common 'wall' time, we need to
    use the UTC offset of the *previous* Transition.
    """
    # Bootstrap the transition with the first transition, effectively
    # extending the first transition backwards to -infinity. This won't be
    # 100% correct with respect to the TZ Database but it will be good
    # enough for the first transition that we care about.
    prev = transitions[0].copy()
    for transition in transitions:
        (
            transition.transition_time_w,
            transition.transition_time_s,
            transition.transition_time_u,
        ) = _expand_date_tuple(
            transition.transition_time,
            prev.offset_seconds,
            prev.delta_seconds,
        )
        prev = transition


def _create_transition_for_year(
    year: int,
    rule: ZoneRule,
    match: MatchingEra,
) -> Transition:
    """Create the transition from the given 'rule' for the given 'year'.
    Transition object is a replica of the underlying Match object, with
    additional bookkeeping info.
    """
    transition = Transition(
        matching_era=match,
        transition_time=_get_transition_time(year, rule),
    )
    transition.zone_rule = rule
    return transition


def _get_interior_years(
    from_year: int,
    to_year: int,
    start_year: int,
    end_year: int,
) -> List[int]:
    """Return the Rule years that overlap with the Match[start_year, end_year].
    """
    years = []
    for year in range(start_year, end_year + 1):
        if from_year <= year and year <= to_year:
            years.append(year)
    return years


def _get_most_recent_prior_year(
    from_year: int,
    to_year: int,
    start_year: int,
    end_year: int,
) -> int:
    """Return the most recent prior year of the rule[from_year, to_year].
    Return INVALID_YEAR if the rule[from_year, to_year] has no prior year to the
    match[start_year, end_year].
    """
    if from_year < start_year:
        if to_year < start_year:
            return to_year
        else:
            return start_year - 1
    else:
        return INVALID_YEAR


def _compare_transition_to_match(
    transition: Transition,
    match: MatchingEra,
) -> int:
    """Determine how the given 'transition' compares to the given 'match' in the
    timeline. The return type is one of the MATCH_STATUS_* constant. There are 4
    cases:

    * MATCH_STATUS_FAR_PAST
        * (not used in this method)
    * MATCH_STATUS_PRIOR
        * The transition occurs before the given 'match'.
    * MATCH_STATUS_EXACT_MATCH
        * The transition occurs exactly at the same time as the start time
          of the given match.
        * The meaning of "exact" seems to be a bit fuzzy and not explained
          very well in the TBDB files. As far as I can tell, an exact match
          occurs when any of the 'w', 's' or 'u' times of the transition occurs
          at the same time as the corresponding 'w', 's' or 'u' times of the
          given 'match'.
    * MATCH_STATUS_WITHIN_MATCH
        * The transition falls within the [start, until) time interval of
          the given 'match'.
    * MATCH_STATUS_FAR_FUTURE
        * The transition falls after the given 'match'.

    Before this method is called, the Transition.transition_time must have been
    expanded into the 'w', 's', and 'u' versions through
    _fix_transition_times().
    """

    # Determine the UTC offset of the previous MatchingEra.
    if match.prev_match:
        prev_match = match.prev_match
        assert prev_match.last_transition is not None
        offset_seconds = prev_match.last_transition.offset_seconds
        delta_seconds = prev_match.last_transition.delta_seconds
    else:
        # The first MatchingEra, so there is no previous Transition. Let's just
        # take the current offset_seconds, and assume a DST offset of 0.
        prev_match = match
        offset_seconds = match.zone_era['offset_seconds']
        delta_seconds = 0

    # Expand the MatchingEra.start_date_time into 'w', 's' and 'u' units.
    (stw, sts, stu) = _expand_date_tuple(
        match.start_date_time,
        offset_seconds,
        delta_seconds,
    )

    # Determine if the Transition happens at exactly the same time as the
    # start of the MatchingEra. An exact match is considered to happen if
    # *any* of the 'w', 's' or 'u' times match up.
    if (
        transition.transition_time_u == stu
        or transition.transition_time_w == stw
        or transition.transition_time_s == sts
    ):
        return MATCH_STATUS_EXACT_MATCH

    if transition.transition_time_u < stu:
        return MATCH_STATUS_PRIOR

    # Check if the transition occurs after the given 'match'. The
    # 'until_date_time' of the current match uses the same UTC offsets as the
    # transition_time of the given 'transition', so we don't have to make any
    # complicated adjustments.
    match_until = match.until_date_time
    if match_until.f == 'w':
        transition_time = transition.transition_time_w
    elif match_until.f == 's':
        transition_time = transition.transition_time_s
    elif match_until.f == 'u':
        transition_time = transition.transition_time_u
    else:
        raise Exception(f"Unknown suffix: {match_until.f}")
    if match_until <= transition_time:
        return MATCH_STATUS_FAR_FUTURE

    return MATCH_STATUS_WITHIN_MATCH


def _compare_transition_to_match_fuzzy(
    transition: Transition,
    match: MatchingEra,
) -> int:
    """Like _compare_transition_to_match() except perform a fuzzy match
    within at least one-month of the match.start or match.until. This is useful
    because unlike _compare_transition_to_match(), the Transition object does
    not need its 'transition_time' to be "fixed" (through
    _fix_transition_times()) to be able to use this function, so we can use this
    function earlier in the filtering process of finding candidate transitions.

    Return:
        * MATCH_STATUS_PRIOR if less than match
        * MATCH_STATUS_WITHIN_MATCH if within match,
        * MATCH_STATUS_FAR_FUTURE if greater than match
        * MATCH_STATUS_EXACT_MATCH is never returned since we cannot make a
          direct comparison to match_start.
    """
    tt = transition.transition_time
    transition_time = 12 * tt.y + tt.M

    ms = match.start_date_time
    match_start = 12 * ms.y + ms.M
    if transition_time < match_start - 1:
        return MATCH_STATUS_PRIOR

    mu = match.until_date_time
    match_until = 12 * mu.y + mu.M
    if match_until + 2 <= transition_time:
        return MATCH_STATUS_FAR_FUTURE

    return MATCH_STATUS_WITHIN_MATCH


def _get_transition_time(year: int, rule: ZoneRule) -> DateTuple:
    """Return the (year, month, day, seconds, suffix) of the Rule in given
    year.
    """
    if year == MIN_YEAR:
        return DateTuple(y=year, M=1, d=1, ss=0, f='w')

    month, day = calc_day_of_month(
        year,
        rule['in_month'],
        rule['on_day_of_week'],
        rule['on_day_of_month']
    )
    seconds = rule['at_seconds']
    suffix = rule['at_time_suffix']
    return DateTuple(y=year, M=month, d=day, ss=seconds, f=suffix)
