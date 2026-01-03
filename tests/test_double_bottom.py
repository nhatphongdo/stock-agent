import unittest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools.price_patterns import _detect_double_bottom


class TestDoubleBottom(unittest.TestCase):
    def setUp(self):
        self.base_date = datetime(2023, 1, 1)

    def test_double_bottom_happy_path(self):
        """Test detection of a standard Double Bottom."""
        # Pattern: Trough 1 (100) -> Peak (120) -> Trough 2 (101)
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        pivot_lows = pd.Series({dates[2]: 100.0, dates[10]: 101.0})  # Similar to 100
        pivot_highs = pd.Series({dates[6]: 120.0})  # Peak between

        df = pd.DataFrame(
            index=dates, columns=["open", "high", "low", "close", "volume"]
        )
        df["low"] = 90
        df["high"] = 130

        patterns = _detect_double_bottom(df, pivot_highs, pivot_lows)

        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0]["type"], "double_bottom")
        self.assertEqual(patterns[0]["neckline"], 120.0)
        self.assertAlmostEqual(patterns[0]["troughs"][0], 100.0)

    def test_double_bottom_failed_dissimilar_troughs(self):
        """Test rejection when troughs are too different."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        pivot_lows = pd.Series(
            {dates[2]: 100.0, dates[10]: 115.0}  # Too high > 5% diff
        )
        pivot_highs = pd.Series({dates[6]: 120.0})

        df = pd.DataFrame(index=dates)
        patterns = _detect_double_bottom(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_double_bottom_failed_no_peak(self):
        """Test rejection when no peak exists between troughs."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        pivot_lows = pd.Series({dates[2]: 100.0, dates[10]: 100.0})
        pivot_highs = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))  # Empty

        df = pd.DataFrame(index=dates)
        patterns = _detect_double_bottom(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_double_bottom_boundary_tolerance_pass(self):
        """Test boundary: Troughs exactly at or within 2% tolerance."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # 100 and 102 (2% diff). Should pass.
        pivot_lows = pd.Series({dates[2]: 100.0, dates[10]: 102.0})
        pivot_highs = pd.Series({dates[6]: 120.0})

        df = pd.DataFrame(
            index=dates, columns=["open", "high", "low", "close", "volume"]
        )
        df["high"] = 130.0
        df["low"] = 90.0

        patterns = _detect_double_bottom(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 1)

    def test_double_bottom_boundary_tolerance_fail(self):
        """Test boundary: Troughs just outside 2% tolerance."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # 100 and 102.1 (2.1% diff). Should fail.
        pivot_lows = pd.Series({dates[2]: 100.0, dates[10]: 102.1})
        pivot_highs = pd.Series({dates[6]: 120.0})

        df = pd.DataFrame(
            index=dates, columns=["open", "high", "low", "close", "volume"]
        )

        patterns = _detect_double_bottom(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_double_bottom_boundary_duration_pass(self):
        """Test boundary: Duration exactly minimum (5 candles)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Index 2 and Index 7. Diff = 5. Should pass.
        pivot_lows = pd.Series({dates[2]: 100.0, dates[7]: 100.0})
        pivot_highs = pd.Series({dates[4]: 120.0})

        df = pd.DataFrame(
            index=dates, columns=["open", "high", "low", "close", "volume"]
        )
        df["high"] = 130.0
        df["low"] = 90.0

        patterns = _detect_double_bottom(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 1)

    def test_double_bottom_boundary_duration_fail(self):
        """Test boundary: Duration just below minimum (4 candles)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Index 2 and Index 6. Diff = 4. Should fail.
        pivot_lows = pd.Series({dates[2]: 100.0, dates[6]: 100.0})
        pivot_highs = pd.Series({dates[4]: 120.0})

        df = pd.DataFrame(
            index=dates, columns=["open", "high", "low", "close", "volume"]
        )

        patterns = _detect_double_bottom(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)


if __name__ == "__main__":
    unittest.main()
