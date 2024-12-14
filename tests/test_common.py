import unittest

from acetime.common import days_in_year_month
from acetime.common import to_epoch_seconds
from acetime.common import to_unix_seconds
from acetime.common import seconds_to_abbrev


class TetCommon(unittest.TestCase):
    def test_days_in_month(self) -> None:
        self.assertEqual(31, days_in_year_month(2000, 1))
        self.assertEqual(29, days_in_year_month(2000, 2))  # 2000 is leap
        self.assertEqual(28, days_in_year_month(2001, 2))
        self.assertEqual(29, days_in_year_month(2004, 2))
        self.assertEqual(28, days_in_year_month(2100, 2))  # 2100 is not leap

    def test_epoch_conversions(self) -> None:
        # epoch_seconds==0 corresponds to 2050-01-01, which is
        # 2524608000 according to (date +%s -d '2050-01-01T00:00:00Z').
        self.assertEqual(2524608000, to_unix_seconds(0))

        # unix_seconds==0 corresponds to 1970-01-01 which should correspond
        # to -2524608000.
        self.assertEqual(-2524608000, to_epoch_seconds(0))

    def test_seconds_to_abbrev(self) -> None:
        self.assertEqual("+00", seconds_to_abbrev(0))

        self.assertEqual("+01", seconds_to_abbrev(3600))
        self.assertEqual("-01", seconds_to_abbrev(-3600))

        self.assertEqual("+0102", seconds_to_abbrev(3720))
        self.assertEqual("-0102", seconds_to_abbrev(-3720))

        self.assertEqual("+010203", seconds_to_abbrev(3723))
        self.assertEqual("-010203", seconds_to_abbrev(-3723))

        self.assertEqual("+000001", seconds_to_abbrev(1))
        self.assertEqual("-000001", seconds_to_abbrev(-1))
