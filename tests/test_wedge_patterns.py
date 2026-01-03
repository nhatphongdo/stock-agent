import unittest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools.price_patterns import _detect_wedge_patterns


class TestWedgePatterns(unittest.TestCase):
    def setUp(self):
        self.base_date = datetime(2023, 1, 1)

    def test_rising_wedge(self):
        """Test Rising Wedge: Both rising, converging."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Highs rising slower: 100, 102, 103, 103.5 -> Slope +small
        # Lows rising faster: 90, 93, 96, 99 -> Slope +large
        # Wait, Rising Wedge logic says "Resistance rising slower than Support" check?
        # Let's check logic in _detect_wedge_patterns:
        # "Resistance rising slower than Support" -> high_slope < low_slope.
        # Check code line 1217: if high_slope_norm < low_slope_norm:

        pivot_highs = pd.Series(
            {dates[2]: 100.0, dates[6]: 102.0, dates[10]: 103.5, dates[14]: 104.5}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 94.0, dates[12]: 98.0, dates[16]: 102.0}
        )

        df = pd.DataFrame(index=dates)
        df["close"] = 103.0

        patterns = _detect_wedge_patterns(df, pivot_highs, pivot_lows)
        found = any(p["type"] == "rising_wedge" for p in patterns)
        self.assertTrue(found)

    def test_falling_wedge(self):
        """Test Falling Wedge: Both falling, converging."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Highs falling faster than Lows
        # Code line 1224: if high_slope_norm < low_slope_norm (more negative < less negative?)
        # Let's re-read logic: "Resistance falling faster (more negative) than Support"
        # e.g -10.0 < -5.0. True.

        pivot_highs = pd.Series(
            {dates[2]: 110.0, dates[6]: 105.0, dates[10]: 100.0, dates[14]: 95.0}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 89.0, dates[12]: 88.0, dates[16]: 87.0}
        )

        df = pd.DataFrame(index=dates)
        df["close"] = 90.0

        patterns = _detect_wedge_patterns(df, pivot_highs, pivot_lows)
        found = any(p["type"] == "falling_wedge" for p in patterns)
        self.assertTrue(found)

    def test_wedge_failed_channel(self):
        """Test rejection when lines are parallel (Channel)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Slopes equal
        pivot_highs = pd.Series(
            {dates[2]: 100.0, dates[6]: 102.5, dates[10]: 105.0, dates[14]: 107.5}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 92.0, dates[12]: 94.0, dates[16]: 96.0}
        )

        df = pd.DataFrame(index=dates)
        df["close"] = 100.0
        patterns = _detect_wedge_patterns(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_wedge_boundary_slope_threshold_pass(self):
        """Test boundary: Slopes just above 0.05 threshold (Rising)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # High slope ~ 0.06 (Norm). > 0.05.
        # Avg Price ~100.
        # 12 candles * 0.06 = 0.72.
        pivot_highs = pd.Series({dates[2]: 100.0, dates[14]: 100.72})
        # Low slope ~ 0.10. > 0.05. And > High slope (Converging).
        # 12 * 0.10 = 1.2.
        pivot_lows = pd.Series({dates[2]: 90.0, dates[14]: 91.2})

        df = pd.DataFrame(index=dates)
        df["close"] = 100.0

        patterns = _detect_wedge_patterns(df, pivot_highs, pivot_lows)
        found = any(p["type"] == "rising_wedge" for p in patterns)
        self.assertTrue(found)

    def test_wedge_boundary_slope_threshold_fail(self):
        """Test boundary: One slope insufficient (<= 0.05)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # High slope ~ 0.04. Too flat.
        pivot_highs = pd.Series({dates[2]: 100.0, dates[14]: 100.48})
        # Low slope ~ 0.10.
        pivot_lows = pd.Series({dates[2]: 90.0, dates[14]: 91.2})

        df = pd.DataFrame(index=dates)
        df["close"] = 100.0

        patterns = _detect_wedge_patterns(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)


if __name__ == "__main__":
    unittest.main()
