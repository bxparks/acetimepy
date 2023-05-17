# Copyright 2018 Brian T. Park
#
# MIT License

"""
Data structure to store and saerch the DST transitions for a given time zone.
"""

import logging
from typing import List
from typing import Optional

from .common import seconds_to_hms
from .date_tuple import DateTuple
from .date_tuple import date_tuple_to_string
from .typing import ZoneRule
from .typing import ZoneEra


NULL_DATE_TUPLE = DateTuple(0, 0, 0, 0, 'w')


class MatchingEra:
    """A version of ZoneEra that overlaps with the [start, end) interval of
    interest. The interval is usually a 14-month interval that begins a month
    before the year of interest, and extends a month after the year of interest.
    """
    def __init__(
        self, *,
        start_date_time: DateTuple,
        until_date_time: DateTuple,
        zone_era: ZoneEra,
        prev_match: Optional['MatchingEra'] = None,
    ):
        # until_date_time of the previous ZoneEra, bounded by viewing window
        self.start_date_time = start_date_time

        # until_date_time of the current ZoneEra, bounded by viewing window
        self.until_date_time = until_date_time

        # the ZoneEra corresponding to this match
        self.zone_era = zone_era

        # the previous MatchingEra whose last_transition will be used to
        # normalize the start_date_time of the current MatchingEra
        self.prev_match = prev_match

        # the last Transition of this Matching Era, which will be used to
        # normalize the start_date_time of the next MatchingEra
        self.last_transition: Optional['Transition'] = None

    def __repr__(self) -> str:
        return (
            'MatchingEra('
            f'start: {date_tuple_to_string(self.start_date_time)}'
            f'; until: {date_tuple_to_string(self.until_date_time)}'
            f'; policy: {policy_name_of(self.zone_era)}'
            ')'
        )


class Transition:
    """A description of a potential change in DST offset. It can come from
    a number of sources:

    1) An instance of a ZoneRule that was referenced by the RULES column,
       instantiated for the given year, which then determines the start date
       and until date.
    2) A boundary between one ZoneEra and the next ZoneEra.
    3) A ZoneRule that has been shifted to the boundary of a ZoneEra.
    """
    def __init__(
        self, *,
        matching_era: MatchingEra,
        transition_time: DateTuple,
    ):
        # The transition times for both simple Match and named Match. (1) For a
        # simple Transition, the transition_time is the startTime of the
        # ZoneEra. (2) For a named Transition, the transition_time is the AT
        # field of the corresponding ZoneRule (see
        # _create_transition_for_year()).
        self.transition_time = transition_time
        self.matching_era = matching_era

        # The start and until times are initially copied from MatchingEra:
        #
        # * start_date_time
        #       * UNTIL time of the *previous* ZoneEra
        # * until_date_time
        #       * UNTIL time of the *current* ZoneEra
        #
        # Then the transition time fields are generated. Then these fields are
        # updated in-situ by _generate_start_until_times() in the following way:
        #
        # * start_date_time
        #       * set to the current wall transition_time converted using the
        #         UTC offset of the current Transition.
        # * until_date_time
        #       * set to the wall transition_time of the *next* Transition using
        #       * the UTC offset of the *current* Transition
        self.start_date_time = matching_era.start_date_time
        self.until_date_time = matching_era.until_date_time

        # the 'w', 's' and 'u' versions of 'transition_time'
        self.transition_time_w = NULL_DATE_TUPLE
        self.transition_time_s = NULL_DATE_TUPLE
        self.transition_time_u = NULL_DATE_TUPLE

        # If the Transition is a prior Transition or an exact matching
        # Transition, its transition_time is clobbered to the start time of the
        # current MatchingEra. When that happens, this field preserves the
        # original transition time for debugging. Not used by any subsequent
        # calculation.
        self.original_transition_time = NULL_DATE_TUPLE

        # The epoch second of start_date_time, which should be the same as the
        # epoch second of transition_time.
        self.start_epoch_second = 0

        # Human-readable timezone abbreviation for the given Transition.
        self.abbrev = ''

        # If this Transition was created from MatchingEra with a named
        # ZonePolicy, this points to the ZoneRule that generated this. For a
        # simple MatchingEra, this will be None.
        self.zone_rule: Optional[ZoneRule] = None

        # Transition compared to its enclosing MatchingEra. See MATCH_STATUS_*
        # parameters and _process_transition_match_status().
        self.match_status: int = 0

    @property
    def format(self) -> str:
        return self.matching_era.zone_era['format']

    @property
    def offset_seconds(self) -> int:
        return self.matching_era.zone_era['offset_seconds']

    @property
    def letter(self) -> str:
        return self.zone_rule['letter'] if self.zone_rule else ''

    @property
    def delta_seconds(self) -> int:
        if self.zone_rule:
            return self.zone_rule['delta_seconds']
        else:
            return self.matching_era.zone_era['era_delta_seconds']

    def copy(self) -> 'Transition':
        result = self.__class__.__new__(self.__class__)
        result.matching_era = self.matching_era
        result.start_date_time = self.start_date_time
        result.until_date_time = self.until_date_time
        result.transition_time = self.transition_time
        result.transition_time_w = self.transition_time_w
        result.transition_time_s = self.transition_time_s
        result.transition_time_u = self.transition_time_u
        result.original_transition_time = self.original_transition_time
        result.start_epoch_second = self.start_epoch_second
        result.abbrev = self.abbrev
        result.zone_rule = self.zone_rule
        result.match_status = self.match_status
        return result

    def __repr__(self) -> str:
        sepoch = self.start_epoch_second if self.start_epoch_second else '-'
        policy_name = policy_name_of(self.matching_era.zone_era)
        offset_seconds = self.offset_seconds
        delta_seconds = self.delta_seconds
        abbrev = self.abbrev if self.abbrev else ''

        # yapf: disable
        if policy_name == 'None':
            return (
                'T('
                f"start={sepoch}"
                f"; match={self.match_status}"
                f"; tt={date_tuple_to_string(self.transition_time)}"
                f"; ttw={date_tuple_to_string(self.transition_time_w)}"
                f"; st={date_tuple_to_string(self.start_date_time)}"
                f"; ut={date_tuple_to_string(self.until_date_time)}"
                f"; {to_utc_string(offset_seconds, delta_seconds)}"
                f"; rule={policy_name}"
                f"; ab={abbrev})"
            )
        else:
            delta_seconds = self.delta_seconds
            zone_rule = self.zone_rule
            assert zone_rule is not None
            zone_rule_from = zone_rule['from_year']
            zone_rule_to = zone_rule['to_year']
            original_transition = (
                date_tuple_to_string(self.original_transition_time)
                if self.original_transition_time
                else ''
            )

            return (
                'T('
                f"start={sepoch}"
                f"; match={self.match_status}"
                f"; tt={date_tuple_to_string(self.transition_time)}"
                f"; ttw={date_tuple_to_string(self.transition_time_w)}"
                f"; st={date_tuple_to_string(self.start_date_time)}"
                f"; ut={date_tuple_to_string(self.until_date_time)}"
                f"; {to_utc_string(offset_seconds, delta_seconds)}"
                f"; rule={policy_name}[{zone_rule_from},{zone_rule_to}]"
                f"; ab={abbrev})"
                f"; ot={original_transition}"
            )
        # yapf: enable


class TransitionStorage:
    """A heap manager of Transition objects, equivalent to the C++
    ExtendedZoneProcessor.TransitionStorage class. There are 4 pools of
    Transition entries:

    1) Active pool: [0, index_prior)
    2) Prior pool: [index_prior, index_candidates), either 0 or 1 element
    3) Candidate pool: [index_candidates, index_free)
    4) Free pool: [index_free, len(transitions))

    The 'high_water' is the largest index used by the TransitionStorage buffer,
    so the minimum required size of buffer is 'high_water + 1'.

    """
    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        """Active pool  at [0, free).
        Free pool at [free, max).
        Max gives the size of stack.
        """
        self.index_free = 0
        self.index_beyond = 0  # index beyond the free pool, i.e. max buf size

    def push_transitions(self, delta: int) -> None:
        """Push imaginary Transitions of size 'delta' into the stack."""
        self.index_free += delta
        if self.index_free > self.index_beyond:
            self.index_beyond = self.index_free

    def pop_transitions(self, delta: int) -> None:
        """Remove imaginary Transitions of size 'delta' from stack."""
        self.index_free -= delta


def check_transitions_sorted(name: str, transitions: List[Transition]) -> None:
    """Check transitions are sorted.
    """
    prev = None
    for transition in transitions:
        if not prev:
            prev = transition
            continue
        if prev.transition_time > transition.transition_time:
            print_transitions(
                f'Policy {name}: Unsorted Transitions',
                transitions)
            raise Exception('Transitions not sorted')


def policy_name_of(era: ZoneEra) -> str:
    """Return the effective policy name of the given ZoneEra."""
    zone_policy = era.get('zone_policy')
    if zone_policy:
        return zone_policy['name']
    else:
        return 'None'


def print_transitions(header: str, transitions: List[Transition]) -> None:
    logging.info('%s: count: %d', header, len(transitions))
    for t in transitions:
        logging.info(t)


def to_utc_string(utcoffset: int, dstoffset: int) -> str:
    return (
        'UTC'
        f'{seconds_to_hm_string(utcoffset)}'
        f'{seconds_to_hm_string(dstoffset)}'
    )


def seconds_to_hm_string(secs: int) -> str:
    if secs < 0:
        hms = seconds_to_hms(-secs)
        return f'-{hms[0]:02}:{hms[1]:02}'
    else:
        hms = seconds_to_hms(secs)
        return f'+{hms[0]:02}:{hms[1]:02}'
