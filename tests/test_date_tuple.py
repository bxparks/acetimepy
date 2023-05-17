# Copyright 2018 Brian T. Park
#
# MIT License

import unittest

from acetime.date_tuple import subtract_date_tuple
from acetime.date_tuple import DateTuple


class TestDateTuple(unittest.TestCase):
    def test_subtract_date_tuple(self) -> None:
        self.assertEqual(
            -1,
            subtract_date_tuple(
                DateTuple(2000, 1, 1, 43, 'w'),
                DateTuple(2000, 1, 1, 44, 'w'),
            )
        )

        self.assertEqual(
            24 * 3600 - 1,
            subtract_date_tuple(
                DateTuple(2000, 1, 2, 43, 'w'),
                DateTuple(2000, 1, 1, 44, 'w'),
            )
        )

        self.assertEqual(
            -31 * 24 * 3600 + 24 * 3600 - 1,
            subtract_date_tuple(
                DateTuple(2000, 1, 2, 43, 'w'),
                DateTuple(2000, 2, 1, 44, 'w'),
            )
        )
