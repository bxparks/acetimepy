import unittest

from acetime.common import days_in_year_month


class TetCommon(unittest.TestCase):
    def test_days_in_month(self) -> None:
        self.assertEqual(31, days_in_year_month(2000, 1))
        self.assertEqual(29, days_in_year_month(2000, 2))  # 2000 is leap
        self.assertEqual(28, days_in_year_month(2001, 2))
        self.assertEqual(29, days_in_year_month(2004, 2))
        self.assertEqual(28, days_in_year_month(2100, 2))  # 2100 is not leap
