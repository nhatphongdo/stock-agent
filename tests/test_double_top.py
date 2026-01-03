import unittest
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools.price_patterns import _detect_double_top


class TestDoubleTop(unittest.TestCase):
    def setUp(self):
        self.base_date = datetime(2023, 1, 1)

    def create_mock_data(self, prices):
        """Create mock DataFrame and pivot Series."""
        dates = [self.base_date + timedelta(days=i) for i in range(len(prices))]
        df = pd.DataFrame(
            {
                "open": prices,
                "high": prices,
                "low": [p * 0.9 for p in prices],
                "close": prices,
                "volume": [1000] * len(prices),
            },
            index=dates,
        )

        # Manually create pivots to simulate detection
        # usage: prices list should have peaks at checking indices
        return df

    def test_double_top_happy_path(self):
        """Test detection of a standard Double Top."""
        # Pattern: Peak 1 (100) -> Valley (80) -> Peak 2 (99)
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Pivots
        pivot_highs = pd.Series(
            {dates[2]: 100.0, dates[10]: 99.0}  # Peak 1  # Peak 2 (similar)
        )
        pivot_lows = pd.Series({dates[6]: 80.0})  # Valley

        # Mock DF (minimal needed for index/loc checks)
        df = pd.DataFrame(
            index=dates, columns=["open", "high", "low", "close", "volume"]
        )
        df["high"] = 90  # Default
        df["low"] = 70

        # Match pattern checks
        patterns = _detect_double_top(df, pivot_highs, pivot_lows)

        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0]["type"], "double_top")
        self.assertEqual(patterns[0]["neckline"], 80.0)
        self.assertEqual(patterns[0]["peaks"], [100.0, 99.0])

    def test_double_top_failed_dissimilar_peaks(self):
        """Test rejection when peaks are too different in price."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        pivot_highs = pd.Series(
            {
                dates[2]: 100.0,
                dates[
                    10
                ]: 85.0,  # Too low compared to 100 (15% diff, default tolerance usually <5%)
            }
        )
        pivot_lows = pd.Series({dates[6]: 80.0})

        df = pd.DataFrame(index=dates)

        patterns = _detect_double_top(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_double_top_failed_no_valley(self):
        """Test rejection when no valley exists between peaks."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        pivot_highs = pd.Series({dates[2]: 100.0, dates[10]: 100.0})
        pivot_lows = pd.Series(
            [], dtype=float, index=pd.DatetimeIndex([])
        )  # Empty with proper index type

        df = pd.DataFrame(index=dates)

        patterns = _detect_double_top(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_double_top_edge_too_close(self):
        """Test rejection when peaks are too close (MIN_PATTERN_CANDLES)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Check specific implementation constant, usually often 5-10
        # Assume MIN_PATTERN_CANDLES is > 2
        pivot_highs = pd.Series({dates[2]: 100.0, dates[4]: 100.0})  # Only 2 days diff
        pivot_lows = pd.Series({dates[3]: 90.0})

        df = pd.DataFrame(index=dates)

        patterns = _detect_double_top(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_double_top_boundary_tolerance_pass(self):
        """Test boundary: Peaks exactly at or within 2% tolerance."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # 100 and 98 (2% diff). 2/100 = 0.02. Should pass.
        pivot_highs = pd.Series({dates[2]: 100.0, dates[10]: 98.0})
        pivot_lows = pd.Series({dates[6]: 80.0})

        df = pd.DataFrame(
            index=dates, columns=["open", "high", "low", "close", "volume"]
        )
        df["high"] = 90.0
        df["low"] = 70.0

        patterns = _detect_double_top(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 1)

    def test_double_top_boundary_tolerance_fail(self):
        """Test boundary: Peaks just outside 2% tolerance."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # 100 and 97.9 (2.1% diff). Should fail.
        pivot_highs = pd.Series({dates[2]: 100.0, dates[10]: 97.9})
        pivot_lows = pd.Series({dates[6]: 80.0})

        df = pd.DataFrame(
            index=dates, columns=["open", "high", "low", "close", "volume"]
        )

        patterns = _detect_double_top(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)

    def test_double_top_boundary_duration_pass(self):
        """Test boundary: Duration exactly minimum (5 candles)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Index 2 and Index 7. Diff = 5. Should pass.
        pivot_highs = pd.Series({dates[2]: 100.0, dates[7]: 100.0})
        pivot_lows = pd.Series({dates[4]: 80.0})

        df = pd.DataFrame(
            index=dates, columns=["open", "high", "low", "close", "volume"]
        )
        df["high"] = 90.0
        df["low"] = 70.0

        patterns = _detect_double_top(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 1)

    def test_double_top_boundary_duration_fail(self):
        """Test boundary: Duration just below minimum (4 candles)."""
        dates = [self.base_date + timedelta(days=i) for i in range(20)]

        # Index 2 and Index 6. Diff = 4. Should fail.
        pivot_highs = pd.Series({dates[2]: 100.0, dates[6]: 100.0})
        pivot_lows = pd.Series({dates[4]: 80.0})

        df = pd.DataFrame(
            index=dates, columns=["open", "high", "low", "close", "volume"]
        )

        patterns = _detect_double_top(df, pivot_highs, pivot_lows)
        self.assertEqual(len(patterns), 0)


if __name__ == "__main__":
    unittest.main()
