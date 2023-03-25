# Copyright 2018 Brian T. Park
#
# MIT License

"""
Data structures of the zonedb which are consumed by the ZoneProcessor class.
These data structures are created in-memory by ZoneInfoInliner. They are written
to 'zone_policies.py' and 'zone_infos.py' by AceTimeTools/pygenerator.py
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing_extensions import TypedDict


# A single 'Rule' entry.
class ZoneRule(TypedDict):
    from_year: int  # from year (inclusive)
    to_year: int  # to year (inclusive), 1 to MAX_YEAR (9999) means 'max'
    in_month: int  # month index (1-12)
    on_day_of_week: int  # 1=Monday, 7=Sunday, 0={exact day_of_month match}
    on_day_of_month: int  # (1-31), 0={last dayOfWeek match}
    at_seconds: int  # at_time in seconds since 00:00:00
    at_time_suffix: str  # 's', 'w', 'u'
    delta_seconds: int  # offset from Standard time in seconds
    letter: str  # Usually ('D', 'S', '-'), but sometimes longer
                 # (e.g. 'WAT', 'CAT', 'DD', '+00', '+02', 'CST').  # noqa


# A ZonePolicy is a policy_name and its list of rules
class ZonePolicy(TypedDict):
    name: str  # name of policy
    rules: List[ZoneRule]  # list of zone rules


# Map of policy_name to its ZonePolicy
ZonePolicyMap = Dict[str, ZonePolicy]


# A single 'Zone' line in the tz table.
class ZoneEra(TypedDict):
    offset_seconds: int  # offset from UTC/GMT in seconds
    zone_policy: Optional[ZonePolicy]  # ZonePolicy or None
    era_delta_seconds: int  # delta offset from UTC if zone_policy == None
    format: str  # abbreviation format (e.g. 'P%sT', 'E%sT', 'GMT/BST')
    until_year: int  # (exclusive) MAX_UNTIL_YEAR (10000) means 'max'
    until_month: int  # 1-12
    until_day: int  # 1-31
    until_seconds: int  # until_time converted into total seconds
    until_time_suffix: str  # '', 's', 'w', 'u'


# A ZoneInfo is a zone_name and its list of zone eras.
class ZoneInfo(TypedDict, total=False):
    name: str  # name of zone

    # If Zone, 'eras' is the list of zone eras or target zone. If Link, this
    # field is not defined.
    eras: List[ZoneEra]

    # If Link, then 'link_to' points to the target ZoneInfo, causing a Link to
    # be a "symbolic link" that knows what it is pointing to. If Zone, this
    # field is not defined. Unfortunately, mypy does not support recursive
    # types, so we have to make it an 'Any' type.
    link_to: Any


# Map of zone_name to its ZoneInfo.
ZoneInfoMap = Dict[str, ZoneInfo]
