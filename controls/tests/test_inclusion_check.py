"""A missing cell, empty cohort or late training emission cannot pass silently."""
from fractions import Fraction as F
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'controls'))
from inclusion_check import compare_records


class InclusionTests(unittest.TestCase):
    def record(self, *outputs):
        return dict(layer=1, lane=0, result=dict(outputs=list(outputs)))

    def test_final_half_unit_is_checked_for_both_count_and_date(self):
        self.assertEqual(compare_records([self.record(229.75)], {(1, 0): []}, '230')[0]['reason'], 'count')
        boxes = {(1, 0): [(F(229), F('229.5'))]}
        self.assertEqual(compare_records([self.record(229.75)], boxes, '230')[0]['reason'], 'date')

    def test_terminal_cut_is_read_from_the_calendar_and_is_half_open(self):
        boxes = {(1, 0): [(F('249.75'), F('249.75'))]}
        self.assertEqual(compare_records([self.record(249.75, 250)], boxes, '250'), [])
        self.assertEqual(compare_records([self.record(230)], {(1, 0): []}, '230'), [])

    def test_missing_duplicate_and_unexpected_cells_are_rejected(self):
        for records in ([], [self.record(), self.record()],
                        [dict(layer=2, lane=0, result=dict(outputs=[]))]):
            with self.subTest(records=records), self.assertRaises(ValueError):
                compare_records(records, {(1, 0): []}, '230')

    def test_empty_cohort_is_rejected_before_accessing_campaign_or_writing_report(self):
        for count in ('0', '-1'):
            result = subprocess.run([sys.executable, str(ROOT / 'controls/inclusion_check.py'),
                'nonexistent-campaign', 'must-not-be-written.json', '--per-kind', count],
                capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertIn('positive integer', result.stderr)


if __name__ == '__main__':
    unittest.main()
