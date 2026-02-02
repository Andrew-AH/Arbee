import unittest
from freezegun import freeze_time

from libs.utils.datetimes import determine_execution_date

class TestDetermineExecutionDate(unittest.TestCase):
    def test_after_3am(self):
        with freeze_time("2025-01-20 03:30:00"):
            result = determine_execution_date()
            self.assertEqual(result, "20012025")

    def test_before_3am(self):
        with freeze_time("2025-01-20 02:59:59"):
            result = determine_execution_date()
            self.assertEqual(result, "19012025")

    def test_exactly_3am(self):
        with freeze_time("2025-01-20 03:00:00"):
            result = determine_execution_date()
            self.assertEqual(result, "20012025")

if __name__ == "__main__":
    unittest.main()
