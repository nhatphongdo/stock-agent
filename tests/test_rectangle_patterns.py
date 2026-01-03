import unittest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools.price_patterns import _detect_rectangle_patterns


class TestRectanglePatterns(unittest.TestCase):
    def setUp(self):
        self.base_date = datetime(2023, 1, 1)

    def test_rectangle_happy_path(self):
        """Test detection of a perfect Rectangle (flat highs/lows)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        pivot_highs = pd.Series(
            {dates[2]: 110.0, dates[6]: 110.0, dates[10]: 110.0, dates[14]: 110.0}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 90.0, dates[12]: 90.0, dates[16]: 90.0}
        )

        df = pd.DataFrame(index=dates)
        df["close"] = 100.0

        patterns = _detect_rectangle_patterns(df, pivot_highs, pivot_lows)

        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0]["type"], "rectangle")
        # Check trendlines are horizontal
        res_lines = patterns[0]["trendlines"]["resistance"]
        self.assertEqual(res_lines[0]["price"], 110.0)
        self.assertEqual(res_lines[1]["price"], 110.0)

    def test_rectangle_failed_zigzag(self):
        """Test rejection of high variance patterns (Zigzag)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Mean 110 but high variance
        pivot_highs = pd.Series(
            {dates[2]: 120.0, dates[6]: 100.0, dates[10]: 120.0, dates[14]: 100.0}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 90.0, dates[12]: 90.0, dates[16]: 90.0}
        )

        df = pd.DataFrame(index=dates)

        patterns = _detect_rectangle_patterns(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_rectangle_failed_slanted(self):
        """Test rejection of slanted channel (slopes not flat)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Rising
        pivot_highs = pd.Series(
            {dates[2]: 110.0, dates[6]: 112.0, dates[10]: 114.0, dates[14]: 116.0}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 92.0, dates[12]: 94.0, dates[16]: 96.0}
        )

        df = pd.DataFrame(index=dates)

        patterns = _detect_rectangle_patterns(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_rectangle_boundary_variance_pass(self):
        """Test boundary: Variance within 3% tolerance."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Mean 100. Highs at 102.9 and 97.1 (2.9% dev).
        # Note: 97.1 to 102.9 is slope?
        # 12 steps. 97.1 to 102.9. Change 5.8. Slope ~0.5. Too high?
        # Need highs to toggle but regression slope be flat.
        # e.g. 102.0, 98.0, 102.0, 98.0.
        # Mean 100. Max dev 2.0%. Slope ~0. Pass.

        # Let's test max tolerance 2.9%. 102.9.
        pivot_highs = pd.Series(
            {dates[2]: 102.9, dates[6]: 97.1, dates[10]: 97.1, dates[14]: 102.9}
        )
        # Lows flat at 90.
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 90.0, dates[12]: 90.0, dates[16]: 90.0}
        )

        df = pd.DataFrame(index=dates)
        df["close"] = 100.0

        patterns = _detect_rectangle_patterns(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 1)

    def test_rectangle_boundary_variance_fail(self):
        """Test boundary: Variance exceeds 3% tolerance."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Mean 100. Highs at 103.1 and 96.9 (3.1% dev).
        pivot_highs = pd.Series(
            {dates[2]: 103.1, dates[6]: 96.9, dates[10]: 96.9, dates[14]: 103.1}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 90.0, dates[12]: 90.0, dates[16]: 90.0}
        )

        df = pd.DataFrame(index=dates)

        patterns = _detect_rectangle_patterns(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_rectangle_boundary_slope_pass(self):
        """Test boundary: Slope just below flat threshold (0.08)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Slope 0.07.
        # 12 candles * 0.07 = 0.84 change.
        pivot_highs = pd.Series(
            {dates[2]: 100.0, dates[6]: 100.28, dates[10]: 100.56, dates[14]: 100.84}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 90.0, dates[12]: 90.0, dates[16]: 90.0}  # Flat
        )

        df = pd.DataFrame(index=dates)
        df["close"] = 100.0

        patterns = _detect_rectangle_patterns(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 1)

    def test_rectangle_boundary_slope_fail(self):
        """Test boundary: Slope just above flat threshold (0.08)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Slope 0.09.
        # 12 candles * 0.09 = 1.08 change.
        pivot_highs = pd.Series(
            {dates[2]: 100.0, dates[6]: 100.36, dates[10]: 100.72, dates[14]: 101.08}
        )
        pivot_lows = pd.Series(
            {dates[4]: 90.0, dates[8]: 90.0, dates[12]: 90.0, dates[16]: 90.0}
        )

        df = pd.DataFrame(index=dates)

        patterns = _detect_rectangle_patterns(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)


if __name__ == "__main__":
    unittest.main()
