import unittest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools.price_patterns import _detect_head_and_shoulders


class TestHeadAndShoulders(unittest.TestCase):
    def setUp(self):
        self.base_date = datetime(2023, 1, 1)
        self.dummy_columns = ["open", "high", "low", "close", "volume"]

    def test_hs_happy_path(self):
        """Test detection of a standard Head and Shoulders pattern."""
        dates = [self.base_date + timedelta(days=i) for i in range(30)]

        # Structure: LS (100) -> Head (120) -> RS (99)
        pivot_highs = pd.Series(
            {
                dates[5]: 100.0,  # Left Shoulder
                dates[15]: 120.0,  # Head
                dates[25]: 99.0,  # Right Shoulder
            }
        )
        pivot_lows = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))

        # Need neckline data (troughs). The function checks df logic for neckline
        # idx1 (LS) to idx2 (Head) -> finds Date of Min Low between them
        start_idx = 0
        df_len = 30
        df = pd.DataFrame(index=dates, columns=self.dummy_columns)
        df["low"] = 80.0

        # Set low for left neckline (between LS and Head)
        # LS at 5, Head at 15. Min low at 10?
        df.iloc[10, df.columns.get_loc("low")] = 70.0  # Left valley

        # Set low for right neckline (between Head and RS)
        # Head at 15, RS at 25. Min low at 20?
        df.iloc[20, df.columns.get_loc("low")] = 72.0  # Right valley

        patterns = _detect_head_and_shoulders(df, pivot_highs, pivot_lows)

        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0]["type"], "head_and_shoulders")
        self.assertEqual(patterns[0]["head"], 120.0)
        self.assertEqual(patterns[0]["shoulders"], [100.0, 99.0])
        self.assertEqual(patterns[0]["neckline"], 71.0)  # (70+72)/2

    def test_hs_failed_head_too_low(self):
        """Test rejection when Head is not higher than shoulders."""
        dates = [self.base_date + timedelta(days=i) for i in range(30)]

        pivot_highs = pd.Series(
            {
                dates[5]: 100.0,
                dates[15]: 90.0,  # Head lower than shoulders
                dates[25]: 100.0,
            }
        )
        pivot_lows = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))
        df = pd.DataFrame(index=dates, columns=self.dummy_columns)

        patterns = _detect_head_and_shoulders(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_hs_failed_shoulders_dissimilar(self):
        """Test rejection when shoulders are not similar."""
        dates = [self.base_date + timedelta(days=i) for i in range(30)]

        pivot_highs = pd.Series(
            {
                dates[5]: 100.0,
                dates[15]: 120.0,
                dates[25]: 80.0,  # Right shoulder too low vs Left (20% diff)
            }
        )
        pivot_lows = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))
        df = pd.DataFrame(index=dates, columns=self.dummy_columns)

        patterns = _detect_head_and_shoulders(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_hs_boundary_shoulder_tolerance_pass(self):
        """Test boundary: Shoulders differ by exactly 5% (tolerance)."""
        dates = [self.base_date + timedelta(days=i) for i in range(30)]

        # LS=100. RS=95. Diff=5. Max=100. 5/100 = 0.05. Should pass.
        pivot_highs = pd.Series({dates[5]: 100.0, dates[15]: 120.0, dates[25]: 95.0})
        pivot_lows = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))

        df = pd.DataFrame(index=dates, columns=self.dummy_columns)
        df["low"] = 80.0

        patterns = _detect_head_and_shoulders(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 1)

    def test_hs_boundary_shoulder_tolerance_fail(self):
        """Test boundary: Shoulders differ by > 5%."""
        dates = [self.base_date + timedelta(days=i) for i in range(30)]

        # LS=100. RS=94.9. Diff=5.1. Max=100. 5.1/100 > 0.05. Should fail.
        pivot_highs = pd.Series({dates[5]: 100.0, dates[15]: 120.0, dates[25]: 94.9})
        pivot_lows = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))

        df = pd.DataFrame(index=dates, columns=self.dummy_columns)
        df["low"] = 80.0

        patterns = _detect_head_and_shoulders(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_hs_boundary_duration_pass(self):
        """Test boundary: Duration exactly minimum (5 candles)."""
        dates = [self.base_date + timedelta(days=i) for i in range(30)]

        # LS=2, Head=7 (Diff 5). Head=7, RS=12 (Diff 5).
        pivot_highs = pd.Series({dates[2]: 100.0, dates[7]: 120.0, dates[12]: 100.0})
        pivot_lows = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))

        df = pd.DataFrame(index=dates, columns=self.dummy_columns)
        df["low"] = 80.0

        patterns = _detect_head_and_shoulders(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 1)


if __name__ == "__main__":
    unittest.main()
