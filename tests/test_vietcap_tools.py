import unittest
import os
import sys

# Add the app directory to the path so we can import app.tools.vietcap_tools
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.tools import vietcap_tools

TEST_TICKER = os.environ.get("TEST_TICKER", "VNM")


class TestVietcapTools(unittest.TestCase):

    def test_get_company_list(self):
        print("\nTesting get_company_list...")
        result = vietcap_tools.get_company_list()
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        # Check first item structure
        self.assertIn("ticker", result[0])
        self.assertIn("name", result[0])

    def test_get_companies_by_financial_criteria(self):
        print("\nTesting get_companies_by_financial_criteria...")
        # Test with no filters
        result = vietcap_tools.get_companies_by_financial_criteria()
        self.assertIsInstance(result, list)

        # Test with filters (assuming some companies verify these criteria)
        result_filtered = vietcap_tools.get_companies_by_financial_criteria(
            dividend_rate=0.0, return_rate=0.0
        )
        self.assertIsInstance(result_filtered, list)

    def test_get_companies_by_sector(self):
        print("\nTesting get_companies_by_sector...")
        result = vietcap_tools.get_companies_by_sector(
            "9500", dividend_rate=None, return_rate=None
        )
        self.assertIsInstance(result, list)

    def test_get_company_info(self):
        print(f"\nTesting get_company_info for {TEST_TICKER}...")
        result = vietcap_tools.get_company_info(TEST_TICKER)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("ticker"), TEST_TICKER)

    def test_get_ohlcv_data(self):
        print(f"\nTesting get_ohlcv_data for {TEST_TICKER}...")
        result = vietcap_tools.get_ohlcv_data(TEST_TICKER, count_back=10)
        self.assertIsInstance(result, dict)
        self.assertIn(TEST_TICKER, result)
        self.assertIsInstance(result[TEST_TICKER], list)
        self.assertTrue(len(result[TEST_TICKER]) > 0)

    def test_get_latest_price_batch(self):
        print(f"\nTesting get_latest_price_batch for {[TEST_TICKER]}...")
        result = vietcap_tools.get_latest_price_batch([TEST_TICKER])
        self.assertIsInstance(result, dict)
        if result:
            self.assertIn(TEST_TICKER, result)
            self.assertEqual(result[TEST_TICKER].get("ticker"), TEST_TICKER)

    def test_get_latest_ohlcv(self):
        print(f"\nTesting get_latest_ohlcv for {TEST_TICKER}...")
        result = vietcap_tools.get_latest_ohlcv(TEST_TICKER)
        self.assertIsInstance(result, dict)
        # It might be empty if market is closed or no data, but usually returns something structure-wise or empty dict
        if result:
            # Basic check if keys exist like 'c', 'o', 'h', 'l', 'v' or similar based on tool definition
            pass

    def test_get_ohlcv_by_day(self):
        print(f"\nTesting get_ohlcv_by_day for {TEST_TICKER}...")
        result = vietcap_tools.get_ohlcv_by_day(TEST_TICKER, days=5)
        self.assertIsInstance(result, dict)

    def test_get_technical_indicators(self):
        print(f"\nTesting get_technical_indicators for {TEST_TICKER}...")
        result = vietcap_tools.get_technical_indicators(TEST_TICKER)
        self.assertIsInstance(result, dict)

    def test_get_financial_ratios(self):
        print(f"\nTesting get_financial_ratios for {TEST_TICKER}...")
        result = vietcap_tools.get_financial_ratios("A34")
        self.assertIsInstance(result, dict)
        self.assertIn("ticker", result)
        self.assertIn("ratios", result)
        self.assertIsInstance(result["ratios"], list)

    def test_get_short_financial(self):
        print(f"\nTesting get_short_financial for {TEST_TICKER}...")
        result = vietcap_tools.get_short_financial(TEST_TICKER)
        self.assertIsInstance(result, dict)

    def test_get_last_quarter_financial(self):
        print(f"\nTesting get_last_quarter_financial for {TEST_TICKER}...")
        result = vietcap_tools.get_last_quarter_financial(TEST_TICKER)
        self.assertIsInstance(result, dict)

    def test_get_price_earnings(self):
        print(f"\nTesting get_price_earnings for {TEST_TICKER}...")
        result = vietcap_tools.get_price_earnings(TEST_TICKER)
        self.assertIsInstance(result, dict)
        self.assertIn("ticker", result)
        self.assertIn("earningsHistory", result)
        self.assertIsInstance(result["earningsHistory"], list)

    def test_get_annual_return(self):
        print(f"\nTesting get_annual_return for {TEST_TICKER}...")
        result = vietcap_tools.get_annual_return(TEST_TICKER)
        self.assertIsInstance(result, dict)
        self.assertIn("ticker", result)
        self.assertIn("returns", result)
        self.assertIsInstance(result["returns"], list)

    def test_get_stock_news(self):
        print(f"\nTesting get_stock_news for {TEST_TICKER}...")
        result = vietcap_tools.get_stock_news(TEST_TICKER)
        self.assertIsInstance(result, dict)
        self.assertIn("ticker", result)
        self.assertIn("news", result)
        self.assertIsInstance(result["news"], list)

    def test_get_company_news(self):
        print(f"\nTesting get_company_news for {TEST_TICKER}...")
        result = vietcap_tools.get_company_news(TEST_TICKER)
        self.assertIsInstance(result, dict)

    def test_get_company_events(self):
        print(f"\nTesting get_company_events for {TEST_TICKER}...")
        result = vietcap_tools.get_company_events(TEST_TICKER)
        self.assertIsInstance(result, dict)

    def test_get_stock_events(self):
        print(f"\nTesting get_stock_events for {TEST_TICKER}...")
        result = vietcap_tools.get_stock_events(TEST_TICKER)
        self.assertIsInstance(result, dict)
        self.assertIn("ticker", result)
        self.assertIn("events", result)
        self.assertIsInstance(result["events"], list)

    def test_get_sector_comparison(self):
        print(f"\nTesting get_sector_comparison for {TEST_TICKER}...")
        result = vietcap_tools.get_sector_comparison(TEST_TICKER)
        self.assertIsInstance(result, dict)

    def test_get_all_symbols(self):
        print("\nTesting get_all_symbols...")
        result = vietcap_tools.get_all_symbols()
        self.assertIsInstance(result, dict)

    def test_get_top_tickers(self):
        print("\nTesting get_top_tickers...")
        result = vietcap_tools.get_top_tickers()
        self.assertIsInstance(result, list)
        if len(result) > 0:
            self.assertIn("ticker", result[0])
            self.assertIn("sentiment", result[0])

    def test_get_trending_news(self):
        print("\nTesting get_trending_news...")
        result = vietcap_tools.get_trending_news()
        self.assertIsInstance(result, list)

    def test_get_coverage_universe(self):
        print("\nTesting get_coverage_universe...")
        result = vietcap_tools.get_coverage_universe()
        self.assertIsInstance(result, list)

    def test_get_stock_ohlcv(self):
        print(f"\nTesting get_stock_ohlcv for {TEST_TICKER}...")
        # Need dates
        from datetime import datetime, timedelta

        end = datetime.now()
        start = end - timedelta(days=5)
        start_str = start.strftime("%Y-%m-%d")
        end_str = end.strftime("%Y-%m-%d")

        result = vietcap_tools.get_stock_ohlcv(TEST_TICKER, start_str, end_str)

    def test_get_company_analysis(self):
        print(f"\nTesting get_company_analysis for {TEST_TICKER}...")
        result = vietcap_tools.get_company_analysis(TEST_TICKER)
        self.assertIsInstance(result, list)

    def test_get_analysis_reports(self):
        print(f"\nTesting get_analysis_reports for {TEST_TICKER}...")
        result = vietcap_tools.get_analysis_reports(TEST_TICKER)
        self.assertIsInstance(result, dict)
        self.assertIn("ticker", result)
        self.assertIn("reports", result)
        self.assertIsInstance(result["reports"], list)


if __name__ == "__main__":
    unittest.main()
