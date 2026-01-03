import unittest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools.price_patterns import _detect_inverse_head_and_shoulders


class TestInverseHeadAndShoulders(unittest.TestCase):
    def setUp(self):
        self.base_date = datetime(2023, 1, 1)
        self.dummy_columns = ["open", "high", "low", "close", "volume"]

    def test_inv_hs_happy_path(self):
        """Test detection of a standard Inverse Head and Shoulders pattern."""
        dates = [self.base_date + timedelta(days=i) for i in range(30)]

        # Structure: LS (100) -> Head (80) -> RS (101)
        pivot_lows = pd.Series(
            {
                dates[5]: 100.0,  # Left Shoulder
                dates[15]: 80.0,  # Head (Lower)
                dates[25]: 101.0,  # Right Shoulder
            }
        )
        pivot_highs = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))

        df = pd.DataFrame(index=dates, columns=self.dummy_columns)
        df["high"] = 110.0

        # Set high for left neckline (between LS and Head)
        df.iloc[10, df.columns.get_loc("high")] = 115.0  # Left peak

        # Set high for right neckline (between Head and RS)
        df.iloc[20, df.columns.get_loc("high")] = 113.0  # Right peak

        patterns = _detect_inverse_head_and_shoulders(df, pivot_highs, pivot_lows)

        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0]["type"], "inverse_head_and_shoulders")
        self.assertEqual(patterns[0]["head"], 80.0)
        self.assertEqual(patterns[0]["neckline"], 114.0)  # (115+113)/2

    def test_inv_hs_failed_head_too_high(self):
        """Test rejection when Head is higher than shoulders."""
        dates = [self.base_date + timedelta(days=i) for i in range(30)]

        pivot_lows = pd.Series(
            {dates[5]: 100.0, dates[15]: 105.0, dates[25]: 100.0}  # Head higher
        )
        pivot_highs = pd.Series([], dtype=float, index=pd.DatetimeIndex([]))
        df = pd.DataFrame(index=dates, columns=self.dummy_columns)

        patterns = _detect_inverse_head_and_shoulders(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)


if __name__ == "__main__":
    unittest.main()
