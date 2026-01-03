import unittest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools.price_patterns import _detect_triangle_patterns


class TestTrianglePatterns(unittest.TestCase):
    def setUp(self):
        self.base_date = datetime(2023, 1, 1)

    def test_ascending_triangle(self):
        """Test Ascending Triangle: Flat Highs, Rising Lows."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Highs at ~100. Lows rising: 90, 92, 94, 96
        pivot_highs = pd.Series(
            {dates[2]: 100.0, dates[6]: 100.1, dates[10]: 99.9, dates[14]: 100.0}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 92.0, dates[12]: 94.0, dates[16]: 96.0}
        )

        df = pd.DataFrame(index=dates)
        df["close"] = 98.0  # dummy current price

        patterns = _detect_triangle_patterns(df, pivot_highs, pivot_lows)

        found = any(p["type"] == "ascending_triangle" for p in patterns)
        self.assertTrue(found)

    def test_descending_triangle(self):
        """Test Descending Triangle: Falling Highs, Flat Lows."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Highs falling: 110, 108, 106, 104. Lows ~90
        pivot_highs = pd.Series(
            {dates[2]: 110.0, dates[6]: 108.0, dates[10]: 106.0, dates[14]: 104.0}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 90.1, dates[12]: 89.9, dates[16]: 90.0}
        )

        df = pd.DataFrame(index=dates)
        df["close"] = 92.0

        patterns = _detect_triangle_patterns(df, pivot_highs, pivot_lows)
        found = any(p["type"] == "descending_triangle" for p in patterns)
        self.assertTrue(found)

    def test_symmetrical_triangle(self):
        """Test Symmetrical Triangle: Falling Highs, Rising Lows."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Highs falling: 110 -> 100. Lows rising: 90 -> 100
        pivot_highs = pd.Series(
            {dates[2]: 110.0, dates[6]: 107.0, dates[10]: 104.0, dates[14]: 101.0}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 93.0, dates[12]: 96.0, dates[16]: 99.0}
        )

        df = pd.DataFrame(index=dates)
        df["close"] = 100.0

        patterns = _detect_triangle_patterns(df, pivot_highs, pivot_lows)
        found = any(p["type"] == "symmetrical_triangle" for p in patterns)
        self.assertTrue(found)

    def test_triangle_failed_too_few_points(self):
        """Test rejection with insufficient pivot points."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        pivot_highs = pd.Series({dates[2]: 100.0})  # Only 1 high
        pivot_lows = pd.Series({dates[4]: 90.0, dates[8]: 92.0})

        df = pd.DataFrame(index=dates)
        patterns = _detect_triangle_patterns(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_triangle_boundary_ascending_slope(self):
        """Test boundary: Highs slope just within flat threshold (Ascending)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Highs slope ~0.09 (Norm). < 0.1.
        # Avg Price ~100. Slope ~ 0.09 w.r.t index.
        # Idx 2 to 14 (12 steps). Change = 12 * (0.09/100*100) = 1.08? No.
        # slope = trend_slope. norm = slope/avg*100.
        # slope = 0.09 * 100 / 100 = 0.09 per candle.
        # 12 candles * 0.09 = 1.08 total change.
        pivot_highs = pd.Series({dates[2]: 100.0, dates[14]: 101.08})
        # Lows slope > 0.1. Say 0.2.
        # 12 * 0.2 = 2.4 change.
        pivot_lows = pd.Series({dates[2]: 90.0, dates[14]: 92.4})

        df = pd.DataFrame(index=dates)
        df["close"] = 100.0

        patterns = _detect_triangle_patterns(df, pivot_highs, pivot_lows)
        # Should be Ascending
        found = any(p["type"] == "ascending_triangle" for p in patterns)
        self.assertTrue(found)

    def test_triangle_boundary_symmetrical_transition(self):
        """Test boundary: Highs slope steep enough for Symmetrical."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Highs slope = -0.11 (Norm). < -0.05.
        # Avg ~100. Change = -0.11 per candle.
        # 12 candles * -0.11 = -1.32.
        pivot_highs = pd.Series({dates[2]: 101.32, dates[14]: 100.0})
        # Lows slope > 0.05. Say 0.1.
        pivot_lows = pd.Series({dates[2]: 90.0, dates[14]: 91.2})

        df = pd.DataFrame(index=dates)
        df["close"] = 100.0

        patterns = _detect_triangle_patterns(df, pivot_highs, pivot_lows)
        # Should be Symmetrical (High slope < -0.05 and Low slope > 0.05)
        # Check logic: Highs falling (-0.11 < -0.05), Lows rising (0.1 > 0.05).
        # And NOT Ascending (abs(-0.11) > 0.1? Yes, 0.11 > 0.1).
        found = any(p["type"] == "symmetrical_triangle" for p in patterns)
        self.assertTrue(found)


if __name__ == "__main__":
    unittest.main()
